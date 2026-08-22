"""Idempotency-Key-Middleware fuer POST/PUT (Ticket 0006, BACKEND.md Abschnitt 0.3).

Ein bereits verarbeiteter Schluessel liefert die urspruengliche Antwort mit 200
statt eines zweiten Datensatzes. Abgelegt wird
`(key, user_id, request_hash, response_body, created_utc)` in
`shared_kernel.idempotency_keys`.

## Reservieren, dann arbeiten

Die Zeile entsteht **bevor** die Anfrage verarbeitet wird, nicht danach - als
Reservierung mit `response_body IS NULL`. Das ist der Kern des Verfahrens und
nicht bloss eine Umstellung der Reihenfolge:

Wer zuerst schreibt, hat den Schluessel. Das entscheidet der Unique-Index, in
einem Statement (`ON CONFLICT DO NOTHING RETURNING`) - nicht eine vorgelagerte
Abfrage. Ein `SELECT`, das fragt, was der `INSERT` ohnehin entscheidet, oeffnet
das Wettrennen erst, das es verhindern soll: zwischen Frage und Antwort passt
jede zweite Anfrage (`docs/reflections/exp_keine-vorpruefung-wo-die-gegenseite-entscheidet.md`).

Daraus ergeben sich vier Ausgaenge, wenn die Reservierung scheitert - der
Schluessel ist also schon vergeben:

| Zustand der bestehenden Zeile | Antwort |
|---|---|
| gleicher Nutzer, gleicher Body, Antwort liegt vor | die gespeicherte Antwort, mit 200 |
| gleicher Nutzer, gleicher Body, Antwort steht aus | 409 - die erste Anfrage laeuft noch |
| gleicher Nutzer, **anderer** Body | 409 - derselbe Schluessel fuer etwas anderes |
| **anderer** Nutzer | 409 - der Schluessel ist belegt, mehr erfaehrt er nicht |

Die beiden Wiederverwendungs-Faelle standen bis #95 auf 422, dem IETF-Entwurf
zum `Idempotency-Key`-Header folgend. Der Vertrag des Frontends
(`contracts/pacts/identity/`) verlangt dort ohne Matcher **409**, und wo Vertrag
und Invariante kollidieren, gewinnt der Vertrag - der Entwurf ist ein Entwurf,
der Pact ist die Vorgabe der HTTP-Grenze
(`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`).
Fachlich passt 409 ohnehin besser: der Schluessel steht im Konflikt mit einem
bestehenden Zustand, der Rumpf selbst ist verarbeitbar. BACKEND.md schreibt nur
den Treffer-Fall (200) vor und sagt zu den uebrigen nichts.

Die drei 409-Faelle sind nicht dasselbe und tragen deshalb unterschiedliche
`type`-Bezeichner: `request-in-progress` fuer den laufenden Erstversuch,
`idempotency-key-reused` fuer den belegten Schluessel.

## Was der `request_hash` soll

Er vergleicht, ob hinter demselben Schluessel dieselbe Anfrage steckt. Ohne
diesen Vergleich waere die Spalte Zierde - und ein Client, der einen Schluessel
versehentlich fuer eine **andere** Anfrage wiederverwendet, bekaeme stillschweigend
die Antwort der ersten und hielte seinen zweiten Vorgang fuer erledigt.

## Ein Aufruf ohne Anmeldung belegt seinen Schluessel trotzdem

`request.state.user_id` setzt die JWT-Pipeline aus **Ticket 0012**, die es noch
nicht gibt. Fehlt der Wert, tritt `ANONYMOUS_USER_ID` an seine Stelle, statt die
Anfrage ungeprueft durchzulassen: die Registrierung hat keinen angemeldeten
Nutzer und braucht die Idempotenz gerade dort am dringendsten - ein zweites Mal
abgeschickt entstuende sonst ein zweites Konto. Der Vertrag des Frontends
verlangt fuer den wiederverwendeten Schluessel eine Antwort; ohne diesen Ersatz
kaeme die Anfrage hier nie an (#95).

Fuer den Vergleich heisst das: unter dem Ersatz-Nutzer entscheidet allein der
`request_hash`, ob hinter dem Schluessel dieselbe Anfrage steckt. Genau so ist es
vor der Anmeldung gemeint - wer der Aufrufer ist, weiss vor ihr niemand.

Der Datenbankzugriff laeuft ueber **dieselbe** `AsyncEngine` wie die Slices. Sie
wird nicht in den Konstruktor gereicht, sondern bei jeder Anfrage aus `app.state`
gelesen: die Middleware-Kette baut Starlette auf, **bevor** der Lifespan laeuft,
in dem die Engine entsteht
(`docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`).
"""

import hashlib
import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from typing import Any, final
from uuid import UUID

from sqlalchemy import TextClause, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_409_CONFLICT
from starlette.types import ASGIApp

from src.api.i18n import ResourcesCache, get_language_from_header, translate
from src.api.problem_details import problem
from src.contexts.shared_kernel.time_provider import TimeProvider

logger = logging.getLogger(__name__)

ANONYMOUS_USER_ID = UUID(int=0)
"""Der Nutzer eines Aufrufs, der noch keinen hat.

Die Nil-UUID und kein `NULL` in der Spalte: `user_id` ist `NOT NULL`, und ein
`NULL` verglichen sich nach SQL-Regeln mit nichts - auch nicht mit sich selbst.
Ein fester Wert haelt den Vergleich in `_answer_from_existing` genau so, wie er
fuer angemeldete Nutzer schon funktioniert.
"""

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
IDEMPOTENCY_KEYS_TABLE = "shared_kernel.idempotency_keys"
IDEMPOTENT_METHODS = frozenset({"POST", "PUT"})
CACHEABLE_STATUS_CODES = frozenset({200, 201})

KEY_REUSED_SLUG = "idempotency-key-reused"
REQUEST_IN_PROGRESS_SLUG = "request-in-progress"
"""Die Fehlercodes der beiden Idempotenz-Ausgaenge, als nackter Slug.

Kein fertiger URI: das `tag:`-Praefix setzt `problem()` an, an einer Stelle
fuer die ganze API. Die Zeichenketten stehen ausserdem in
`PRESENTATION_CODES` (`src/main.py`) und in den i18n-Ressourcen - dort ist
ebenfalls der Slug gemeint und nicht der URI.
"""

# So viele Zeichen eines abgelehnten Header-Werts kommen ins Log. Eine UUID hat
# 36 Zeichen; wer sich in einer vertippt hat, sieht seinen Wert damit noch ganz.
LOGGED_KEY_MAX_LENGTH = 64

# Reservierung und Entscheidung in einem Statement: gibt es die Zeile schon,
# kommt nichts zurueck - und genau das ist die Auskunft "ein anderer war
# schneller". Ohne vorgelagertes SELECT gibt es dazwischen kein Zeitfenster.
_CLAIM_KEY: TextClause = text(
    f"""
        INSERT INTO {IDEMPOTENCY_KEYS_TABLE}
            (key, user_id, request_hash, response_body, created_utc)
        VALUES (:key, :user_id, :request_hash, NULL, :created_utc)
        ON CONFLICT (key) DO NOTHING
        RETURNING id
    """  # noqa: S608 -- Parameterized via named bindings
)

# Bewusst nur ueber `key` gesucht, nicht ueber `(key, user_id)`: der
# Unique-Index steht auf `key` allein. Wuerde hier nach `user_id` gefiltert,
# faende die Abfrage bei einem fremden Schluessel nichts - und der Ablauf liefe
# in einen Zustand, den es laut Reservierung gerade nicht geben kann.
_FIND_KEY: TextClause = text(
    f"""
        SELECT user_id, request_hash, response_body
        FROM {IDEMPOTENCY_KEYS_TABLE}
        WHERE key = :key
    """  # noqa: S608 -- Parameterized via named bindings
)

_STORE_RESPONSE: TextClause = text(
    f"""
        UPDATE {IDEMPOTENCY_KEYS_TABLE}
        SET response_body = :response_body
        WHERE key = :key
    """  # noqa: S608 -- Parameterized via named bindings
)

# Gibt die Reservierung wieder frei. Noetig, wenn die Anfrage keine Antwort
# hinterlaesst, die sich wiederholen liesse - sonst blockierte ein einziger
# Fehlschlag den Schluessel dauerhaft, und der Client koennte den Vorgang nie
# erneut versuchen.
_RELEASE_CLAIM: TextClause = text(
    f"""
        DELETE FROM {IDEMPOTENCY_KEYS_TABLE}
        WHERE key = :key AND response_body IS NULL
    """  # noqa: S608 -- Parameterized via named bindings
)


def calculate_request_hash(method: str, path: str, body: str) -> str:
    """Berechne einen SHA256-Hash aus Methode, Pfad und Body.

    Args:
        method: HTTP-Methode (POST, PUT, etc.)
        path: Request-Pfad
        body: Request-Body als String

    Returns:
        SHA256-Hash als hexadezimaler String

    """
    request_string = f"{method}:{path}:{body}"
    return hashlib.sha256(request_string.encode()).hexdigest()


def is_idempotent_method(method: str) -> bool:
    """Prüfe, ob die HTTP-Methode idempotent behandelt werden soll.

    Args:
        method: HTTP-Methode

    Returns:
        True für POST und PUT, False sonst

    """
    return method.upper() in IDEMPOTENT_METHODS


def format_key_for_log(key_header: str) -> str:
    """Bereite einen abgelehnten Idempotency-Key so auf, dass er sich gefahrlos loggen laesst.

    Der Wert ist ungeprueft und beliebig lang; ungekuerzt geloggt macht ihn eine
    einzige Anfrage zu Log-Flooding. Zur Diagnose traegt hinter den ersten
    Zeichen nichts mehr bei - ausser der Laenge des Originals, die deshalb hinter
    der Kuerzung steht.

    Der Wert geht durch `repr` und steht damit in Anfuehrungszeichen; die
    Kuerzungs-Marke steht **ausserhalb** davon. Was vom Aufrufer kommt, endet
    also am schliessenden Anfuehrungszeichen - ein Wert, der selbst wie eine
    Marke aussieht, kann keine vortaeuschen, weil `repr` die Anfuehrungszeichen
    darin maskiert. Dasselbe `repr` haelt Steuerzeichen davon ab, roh ins Log zu
    geraten.

    Args:
        key_header: Der abgelehnte Header-Wert

    Returns:
        Den Wert in Anfuehrungszeichen, solange er `LOGGED_KEY_MAX_LENGTH` nicht
        ueberschreitet; sonst seinen Anfang in Anfuehrungszeichen, gefolgt von
        der Kuerzungs-Marke mit der Laenge des Originals.

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


async def find_key(engine: AsyncEngine, key: UUID) -> Mapping[str, Any] | None:
    """Lies die bestehende Zeile zu einem Schluessel."""
    async with engine.connect() as connection:
        found = await connection.execute(_FIND_KEY, {"key": key})
        return found.mappings().first()


async def store_response(engine: AsyncEngine, key: UUID, response_body: dict[str, Any]) -> None:
    """Halte die Antwort an der Reservierung fest."""
    async with engine.begin() as connection:
        await connection.execute(
            _STORE_RESPONSE, {"key": key, "response_body": json.dumps(response_body)}
        )


async def release_claim(engine: AsyncEngine, key: UUID) -> None:
    """Gib eine Reservierung frei, zu der es keine wiederholbare Antwort gibt."""
    async with engine.begin() as connection:
        await connection.execute(_RELEASE_CLAIM, {"key": key})


@final
class IdempotencyKeyMiddleware(BaseHTTPMiddleware):
    """Middleware für Idempotency-Key-Behandlung.

    Wertet den Idempotency-Key-Header aus und liefert bei Duplikaten
    die ursprüngliche Antwort mit Status 200 statt 201/neue Verarbeitung.
    """

    def __init__(
        self,
        app: ASGIApp,
        time_provider: TimeProvider,
        ttl_days: int = 7,
    ) -> None:
        """Initialisiere die Middleware.

        Args:
            app: Die ASGI-App
            time_provider: TimeProvider fuer den `created_utc`-Zeitstempel
            ttl_days: TTL in Tagen (Standard: 7). Der Cleanup-Job dazu ist
                nicht Teil von Ticket 0006 - der Wert liegt hier als
                Konfiguration bereit, bis es ihn gibt.

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

        # Die Nutzeridentitaet setzt die JWT-Pipeline aus Ticket 0012, die es
        # noch nicht gibt - und bei der Registrierung gibt es sie nie.
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
            # Die Datenbank ist der Schiedsrichter; ist sie nicht erreichbar,
            # gibt es kein Urteil. Die Anfrage deshalb abzulehnen waere schlimmer
            # als sie ohne Idempotenz laufen zu lassen.
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
        language = get_language_from_header(request.headers.get("accept-language"))
        resources: ResourcesCache = request.app.state.resources
        existing = await find_key(engine, key)
        if existing is None:
            # Zwischen Reservierung und Abfrage geloescht (TTL-Bereinigung).
            # Ein Vorgang ohne Absicherung ist besser als ein abgelehnter.
            logger.warning("Idempotency key %s verschwand zwischen Claim und Abfrage", key)
            return await call_next(request)

        if existing["user_id"] != user_id or existing["request_hash"] != request_hash:
            # Fremder Nutzer und abweichender Body sind derselbe Fall: der
            # Schluessel steht fuer etwas anderes. Die Antwort unterscheidet die
            # beiden bewusst nicht - sonst verriete sie, dass der Schluessel
            # jemand anderem gehoert.
            logger.warning("Idempotency key %s fuer eine abweichende Anfrage verwendet", key)
            title = translate(resources, "idempotency-key-reused", language=language)
            detail = translate(resources, "idempotency-key-reused-detail", language=language)
            return problem(
                request,
                HTTP_409_CONFLICT,
                KEY_REUSED_SLUG,
                title,
                detail,
                language_tag=language,
            )

        if existing["response_body"] is None:
            logger.info("Idempotency key %s: die erste Anfrage laeuft noch", key)
            title = translate(resources, "idempotency-request-in-progress", language=language)
            detail = translate(
                resources, "idempotency-request-in-progress-detail", language=language
            )
            return problem(
                request,
                HTTP_409_CONFLICT,
                REQUEST_IN_PROGRESS_SLUG,
                title,
                detail,
                language_tag=language,
            )

        logger.info("Idempotency key %s gefunden, gespeicherte Antwort wird geliefert", key)
        return JSONResponse(content=json.loads(existing["response_body"]), status_code=200)

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
            # Ohne Antwort ist die Reservierung wertlos und wuerde den
            # Schluessel dauerhaft blockieren.
            await release_claim(engine, key)
            raise

        if response.status_code not in CACHEABLE_STATUS_CODES:
            await release_claim(engine, key)
            return response

        # `call_next` liefert eine Streaming-Antwort: der Body ist ein noch nicht
        # gelesener Iterator, kein `.body`. Er muss hier eingesammelt werden - und
        # weil er sich nur einmal lesen laesst, geht anschliessend eine neue
        # Antwort mit denselben Bytes hinaus.
        raw_body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            response_body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Error parsing response body: {e}")  # noqa: G004 -- Parse error for debugging
            await release_claim(engine, key)
            response_body = None

        if response_body is not None:
            await store_response(engine, key, response_body)

        return Response(
            content=raw_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
