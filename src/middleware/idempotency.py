"""Idempotency-Key-Middleware fuer POST/PUT (Ticket 0006, BACKEND.md Abschnitt 0.3).

Bewusste Abweichungen, jeweils mit Entscheidung dahinter:

- Der Replay wiederholt Statuscode und `REPLAYED_HEADERS` des Erstaufrufs, nicht nur
  dessen Rumpf. `docs/Draft/BACKEND.md` Abschnitt 0.3 schreibt woertlich `200` vor;
  siehe `docs/decisions/2026-08-24-1800-idempotenz-replay-wiederholt-den-erstaufruf.md`.
- Die Wiederverwendungs-Faelle antworten mit 409 statt mit dem 422 des IETF-Entwurfs,
  weil der Pact 409 ohne Matcher verlangt
  (`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`).
- Reserviert wird vor der Verarbeitung, in einem Statement, ohne vorgelagertes SELECT
  (`docs/reflections/exp_keine-vorpruefung-wo-die-gegenseite-entscheidet.md`).
- Die `AsyncEngine` kommt bei jeder Anfrage aus `app.state` und nicht aus dem
  Konstruktor: Starlette baut die Middleware-Kette vor dem Lifespan auf
  (`docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`).
"""

import hashlib
import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from typing import Any, Final, final
from uuid import UUID

from sqlalchemy import RowMapping, TextClause, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_409_CONFLICT
from starlette.types import ASGIApp

from src.api.problem_details import translated_problem
from src.contexts.shared_kernel.time_provider import TimeProvider
from src.middleware.streamed_body import read_streamed_body

logger = logging.getLogger(__name__)

ANONYMOUS_USER_ID = UUID(int=0)
"""Der Nutzer eines Aufrufs, der noch keinen hat.

Die Nil-UUID und kein `NULL`: ein `NULL` verglichen sich nach SQL-Regeln mit nichts,
auch nicht mit sich selbst.
"""

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
IDEMPOTENCY_KEYS_TABLE = "shared_kernel.idempotency_keys"
IDEMPOTENT_METHODS = frozenset({"POST", "PUT"})
CACHEABLE_STATUS_CODES = frozenset({200, 201})

REPLAYED_HEADERS: Final = frozenset({"location", "content-language"})
"""Die Kopfzeilen, die zur Antwort gehoeren und deshalb mit ihr aufgezeichnet werden.

Eine Erlaubnisliste, kleingeschrieben, weil HTTP-Feldnamen ohne Ruecksicht auf
Gross-/Kleinschreibung verglichen werden.
"""

KEY_REUSED_SLUG = "idempotency-key-reused"
REQUEST_IN_PROGRESS_SLUG = "request-in-progress"
"""Die Fehlercodes der beiden Idempotenz-Ausgaenge, als nackter Slug.

Kein fertiger URI: das `tag:`-Praefix setzt `problem()` an, an einer Stelle fuer die
ganze API.
"""

# Eine UUID hat 36 Zeichen; wer sich in einer vertippt hat, sieht seinen Wert noch ganz.
LOGGED_KEY_MAX_LENGTH = 64

_CLAIM_KEY: TextClause = text(
    f"""
        INSERT INTO {IDEMPOTENCY_KEYS_TABLE}
            (key, user_id, request_hash, response_body, created_utc)
        VALUES (:key, :user_id, :request_hash, NULL, :created_utc)
        ON CONFLICT (key) DO NOTHING
        RETURNING id
    """  # noqa: S608 -- Parameterized via named bindings
)

# Nur ueber `key` gesucht, nicht ueber `(key, user_id)`: der Unique-Index steht auf
# `key` allein, ein fremder Schluessel muss hier gefunden werden.
_FIND_KEY: TextClause = text(
    f"""
        SELECT user_id, request_hash, response_body, response_status, response_headers
        FROM {IDEMPOTENCY_KEYS_TABLE}
        WHERE key = :key
    """  # noqa: S608 -- Parameterized via named bindings
)

_STORE_RESPONSE: TextClause = text(
    f"""
        UPDATE {IDEMPOTENCY_KEYS_TABLE}
        SET response_body = :response_body,
            response_status = :response_status,
            response_headers = :response_headers
        WHERE key = :key
    """  # noqa: S608 -- Parameterized via named bindings
)

# Ohne Freigabe blockierte ein einziger Fehlschlag den Schluessel dauerhaft.
_RELEASE_CLAIM: TextClause = text(
    f"""
        DELETE FROM {IDEMPOTENCY_KEYS_TABLE}
        WHERE key = :key AND response_body IS NULL
    """  # noqa: S608 -- Parameterized via named bindings
)


def calculate_request_hash(method: str, path: str, body: str) -> str:
    """Berechne einen SHA256-Hash aus Methode, Pfad und Body."""
    request_string = f"{method}:{path}:{body}"
    return hashlib.sha256(request_string.encode()).hexdigest()


def is_idempotent_method(method: str) -> bool:
    """Prüfe, ob die HTTP-Methode idempotent behandelt werden soll."""
    return method.upper() in IDEMPOTENT_METHODS


def format_key_for_log(key_header: str) -> str:
    """Bereite einen abgelehnten Idempotency-Key so auf, dass er sich gefahrlos loggen laesst.

    `repr` maskiert Steuerzeichen und Anfuehrungszeichen; die Kuerzungs-Marke steht
    ausserhalb davon, damit kein Wert eine vortaeuschen kann.
    """
    if len(key_header) <= LOGGED_KEY_MAX_LENGTH:
        return repr(key_header)
    cut = repr(key_header[:LOGGED_KEY_MAX_LENGTH])
    return f"{cut} [gekuerzt, Originallaenge {len(key_header)}]"


async def claim_key(
    engine: AsyncEngine,
    key: UUID,
    user_id: UUID,
    request_hash: str,
    created_utc: datetime,
) -> bool:
    """Reserviere den Schluessel. `True`, wenn er dieser Anfrage gehoert.

    `False` heisst: jemand war schneller - wer und womit, sagt `find_key`.
    """
    async with engine.begin() as connection:
        claimed = await connection.execute(
            _CLAIM_KEY,
            {
                "key": key,
                "user_id": user_id,
                "request_hash": request_hash,
                "created_utc": created_utc,
            },
        )
        return claimed.first() is not None


async def find_key(engine: AsyncEngine, key: UUID) -> RowMapping | None:
    """Lies die bestehende Zeile zu einem Schluessel."""
    async with engine.connect() as connection:
        found = await connection.execute(_FIND_KEY, {"key": key})
        return found.mappings().first()


async def store_response(
    engine: AsyncEngine,
    key: UUID,
    response_body: dict[str, Any],
    response_status: int,
    response_headers: Mapping[str, str],
) -> None:
    """Halte die Antwort an der Reservierung fest."""
    async with engine.begin() as connection:
        await connection.execute(
            _STORE_RESPONSE,
            {
                "key": key,
                "response_body": json.dumps(response_body),
                "response_status": response_status,
                "response_headers": json.dumps(dict(response_headers)),
            },
        )


def replayable_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Waehle aus einer Antwort die Kopfzeilen, die ihre Wiederholung tragen soll."""
    return {name: value for name, value in headers.items() if name.lower() in REPLAYED_HEADERS}


def stored_headers(raw: str | None) -> dict[str, str]:
    """Lies die aufgezeichneten Kopfzeilen zurueck.

    Fehlende oder unlesbare Kopfzeilen ergeben einen Replay ohne sie: unvollstaendig,
    aber besser als eine verweigerte Antwort.
    """
    if raw is None:
        return {}
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"Gespeicherte Kopfzeilen sind unlesbar: {e}")  # noqa: G004 -- Parse error for debugging
        return {}
    return replayable_headers(decoded) if isinstance(decoded, dict) else {}


async def release_claim(engine: AsyncEngine, key: UUID) -> None:
    """Gib eine Reservierung frei, zu der es keine wiederholbare Antwort gibt."""
    async with engine.begin() as connection:
        await connection.execute(_RELEASE_CLAIM, {"key": key})


@final
class IdempotencyKeyMiddleware(BaseHTTPMiddleware):
    """Liefert bei einem wiederverwendeten Idempotency-Key die urspruengliche Antwort."""

    def __init__(
        self,
        app: ASGIApp,
        time_provider: TimeProvider,
        ttl_days: int = 7,
    ) -> None:
        """`ttl_days` liegt als Konfiguration bereit fuer den Cleanup-Job.

        Der Job selbst ist nicht Teil von Ticket 0006.
        """
        super().__init__(app)
        self.time_provider = time_provider
        self.ttl_days = ttl_days

    async def dispatch(  # noqa: PLR0911 -- Early returns for guard conditions
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Verarbeite eine Anfrage unter ihrem Idempotency-Key."""
        if not is_idempotent_method(request.method):
            return await call_next(request)

        if not (idempotency_key_header := request.headers.get(IDEMPOTENCY_KEY_HEADER)):
            return await call_next(request)

        try:
            idempotency_key = UUID(idempotency_key_header)
        except ValueError:
            logger.warning(
                "Invalid Idempotency-Key format: %s", format_key_for_log(idempotency_key_header)
            )
            return await call_next(request)

        # Die Nutzeridentitaet setzt die JWT-Pipeline aus Ticket 0012, die es noch nicht
        # gibt - und bei der Registrierung gibt es sie nie.
        user_id: UUID = getattr(request.state, "user_id", None) or ANONYMOUS_USER_ID

        engine: AsyncEngine | None = getattr(request.app.state, "engine", None)
        if engine is None:
            logger.warning("No database engine available, skipping idempotency check")
            return await call_next(request)

        body_str = ""
        try:
            body_str = (await request.body()).decode("utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.warning(f"Error reading request body: {e}")  # noqa: G004 -- Exception details for debugging

        request_hash = calculate_request_hash(request.method, request.url.path, body_str)

        try:
            claimed = await claim_key(
                engine, idempotency_key, user_id, request_hash, self.time_provider.utc_now()
            )
        except SQLAlchemyError as e:
            # Ohne erreichbare Datenbank gibt es kein Urteil; die Anfrage abzulehnen waere
            # schlimmer, als sie ohne Idempotenz laufen zu lassen.
            logger.warning(f"Error claiming idempotency key: {e}")  # noqa: G004 -- DB error details for diagnostics
            return await call_next(request)

        if not claimed:
            return await self._answer_from_existing(
                request, call_next, engine, idempotency_key, user_id, request_hash
            )

        return await self._process_and_store(request, call_next, engine, idempotency_key)

    async def _answer_from_existing(  # noqa: PLR0913, PLR0917 -- Handler needs request context, engine, and key data
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
        engine: AsyncEngine,
        key: UUID,
        user_id: UUID,
        request_hash: str,
    ) -> Response:
        """Der Schluessel war schon vergeben - entscheide, was der Aufrufer bekommt."""
        existing = await find_key(engine, key)
        if existing is None:
            # Zwischen Reservierung und Abfrage geloescht (TTL-Bereinigung); ein Vorgang
            # ohne Absicherung ist besser als ein abgelehnter.
            logger.warning("Idempotency key %s verschwand zwischen Claim und Abfrage", key)
            return await call_next(request)

        if existing["user_id"] != user_id or existing["request_hash"] != request_hash:
            # Fremder Nutzer und abweichender Body bekommen bewusst dieselbe Antwort -
            # sonst verriete sie, dass der Schluessel jemand anderem gehoert.
            logger.warning("Idempotency key %s fuer eine abweichende Anfrage verwendet", key)
            return translated_problem(
                request,
                HTTP_409_CONFLICT,
                KEY_REUSED_SLUG,
            )

        if existing["response_body"] is None:
            logger.info("Idempotency key %s: die erste Anfrage laeuft noch", key)
            return translated_problem(
                request,
                HTTP_409_CONFLICT,
                REQUEST_IN_PROGRESS_SLUG,
                # Der Slug steht im Pact und wird deshalb nicht an den
                # Ressourcen-Schluessel angeglichen.
                resource_key="idempotency-request-in-progress",
            )

        logger.info("Idempotency key %s gefunden, gespeicherte Antwort wird geliefert", key)
        # `or HTTP_200_OK`: eine Zeile aus der Zeit vor `shared_005` hat keinen
        # aufgezeichneten Status.
        return JSONResponse(
            content=json.loads(existing["response_body"]),
            status_code=existing["response_status"] or HTTP_200_OK,
            headers=stored_headers(existing["response_headers"]),
        )

    async def _process_and_store(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
        engine: AsyncEngine,
        key: UUID,
    ) -> Response:
        """Verarbeite die Anfrage und halte ihre Antwort an der Reservierung fest."""
        try:
            response = await call_next(request)
        except Exception:
            await release_claim(engine, key)
            raise

        if response.status_code not in CACHEABLE_STATUS_CODES:
            await release_claim(engine, key)
            return response

        # Der Strom laesst sich nur einmal lesen, deshalb geht unten eine neue Antwort
        # mit denselben Bytes hinaus.
        raw_body = await read_streamed_body(response)
        try:
            response_body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Error parsing response body: {e}")  # noqa: G004 -- Parse error for debugging
            await release_claim(engine, key)
            response_body = None

        if response_body is not None:
            await store_response(
                engine,
                key,
                response_body,
                response.status_code,
                replayable_headers(response.headers),
            )

        return Response(
            content=raw_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
