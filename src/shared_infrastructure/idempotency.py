"""Idempotency-Key-Middleware fuer POST/PUT (Ticket 0006, BACKEND.md Abschnitt 0.3).

Ein bereits verarbeiteter Schluessel liefert die urspruengliche Antwort mit 200
statt eines zweiten Datensatzes. Abgelegt wird
`(key, user_id, request_hash, response_body, created_utc)` in
`shared_kernel.idempotency_keys`.

Der Datenbankzugriff laeuft ueber **dieselbe** `AsyncEngine` wie die Slices - es
gibt genau einen Weg zur Datenbank im Prozess. Die Engine wird nicht in den
Konstruktor gereicht, sondern bei jeder Anfrage aus `app.state` gelesen: die
Middleware-Kette baut Starlette auf, **bevor** der Lifespan laeuft, in dem die
Engine entsteht. Genau daran ist die frühere Verdrahtung gescheitert (siehe
`docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`).
"""

import hashlib
import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any, final
from uuid import UUID

from sqlalchemy import TextClause, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from src.shared_kernel.time_provider import TimeProvider

logger = logging.getLogger(__name__)

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
IDEMPOTENCY_KEYS_TABLE = "shared_kernel.idempotency_keys"
IDEMPOTENT_METHODS = frozenset({"POST", "PUT"})
CACHEABLE_STATUS_CODES = frozenset({200, 201})

SELECT_IDEMPOTENCY_KEY: TextClause = text(f"""
    SELECT key, user_id, request_hash, response_body, created_utc
    FROM {IDEMPOTENCY_KEYS_TABLE}
    WHERE key = :key AND user_id = :user_id
""")

INSERT_IDEMPOTENCY_KEY: TextClause = text(f"""
    INSERT INTO {IDEMPOTENCY_KEYS_TABLE}
        (key, user_id, request_hash, response_body, created_utc)
    VALUES (:key, :user_id, :request_hash, :response_body, :created_utc)
""")


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


async def get_idempotency_key_from_db(
    engine: AsyncEngine, key: UUID, user_id: UUID
) -> dict[str, Any] | None:
    """Hole einen Idempotency-Key aus der Datenbank.

    Args:
        engine: Die Engine des Prozesses
        key: UUID des Idempotency-Keys
        user_id: UUID des Benutzers

    Returns:
        Dict mit Key-Daten oder None, falls nicht vorhanden
    """
    try:
        async with engine.connect() as connection:
            found = await connection.execute(
                SELECT_IDEMPOTENCY_KEY, {"key": key, "user_id": user_id}
            )
            if (row := found.mappings().first()) is not None:
                return dict(row)
            return None
    except SQLAlchemyError as e:
        logger.warning(f"Error fetching idempotency key: {e}")
        return None


async def save_idempotency_key(
    engine: AsyncEngine,
    key: UUID,
    user_id: UUID,
    request_hash: str,
    response_body: dict[str, Any],
    created_utc: datetime,
) -> bool:
    """Speichere einen neuen Idempotency-Key in der Datenbank.

    Args:
        engine: Die Engine des Prozesses
        key: UUID des Idempotency-Keys
        user_id: UUID des Benutzers
        request_hash: SHA256-Hash des Requests
        response_body: Response-Body als Dict
        created_utc: Zeitpunkt der Speicherung (vom TimeProvider)

    Returns:
        True, falls erfolgreich, False bei Fehler
    """
    try:
        async with engine.begin() as connection:
            await connection.execute(
                INSERT_IDEMPOTENCY_KEY,
                {
                    "key": key,
                    "user_id": user_id,
                    "request_hash": request_hash,
                    "response_body": json.dumps(response_body),
                    "created_utc": created_utc,
                },
            )
        return True
    except SQLAlchemyError as e:
        logger.warning(f"Error saving idempotency key: {e}")
        return False


def is_idempotent_method(method: str) -> bool:
    """Prüfe, ob die HTTP-Methode idempotent behandelt werden soll.

    Args:
        method: HTTP-Methode

    Returns:
        True für POST und PUT, False sonst
    """
    return method.upper() in IDEMPOTENT_METHODS


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

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Verarbeite einen Request mit Idempotency-Key-Unterstützung.

        Args:
            request: Der eingehende Request
            call_next: Die nächste Middleware/Handler

        Returns:
            Eine Response (entweder gekachte oder neue)
        """
        # Nur POST/PUT mit Idempotency-Key verarbeiten
        if not is_idempotent_method(request.method):
            return await call_next(request)

        if not (idempotency_key_header := request.headers.get(IDEMPOTENCY_KEY_HEADER)):
            return await call_next(request)

        # Versuche, den Header als UUID zu parsen
        try:
            idempotency_key = UUID(idempotency_key_header)
        except ValueError:
            logger.warning(f"Invalid Idempotency-Key format: {idempotency_key_header}")
            return await call_next(request)

        # Extrahiere user_id aus Request (z.B. aus JWT oder Context)
        if not (user_id := getattr(request.state, "user_id", None)):
            logger.warning("No user_id in request state, skipping idempotency check")
            return await call_next(request)

        # Berechne RequestHash aus Methode, Pfad und Body
        body_str = ""
        try:
            body_bytes = await request.body()
            body_str = body_bytes.decode("utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.warning(f"Error reading request body: {e}")

        request_hash = calculate_request_hash(request.method, request.url.path, body_str)

        # Die Engine des Prozesses - dieselbe, mit der die Slices schreiben.
        engine: AsyncEngine | None = getattr(request.app.state, "engine", None)
        if engine is None:
            logger.warning("No database engine available, skipping idempotency check")
            return await call_next(request)

        # Prüfe, ob Key bekannt ist
        existing_key = await get_idempotency_key_from_db(engine, idempotency_key, user_id)
        if existing_key:
            logger.info(f"Idempotency key {idempotency_key} found, returning cached response")
            return JSONResponse(
                content=json.loads(existing_key["response_body"]),
                status_code=200,
            )

        # Key ist neu: verarbeite Request normal
        response = await call_next(request)

        if response.status_code not in CACHEABLE_STATUS_CODES:
            return response

        # `call_next` liefert eine Streaming-Antwort: der Body ist ein noch nicht
        # gelesener Iterator, kein `.body`. Er muss hier eingesammelt werden - und
        # weil er sich nur einmal lesen laesst, geht anschliessend eine neue
        # Antwort mit denselben Bytes hinaus.
        raw_body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            response_body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Error parsing response body: {e}")
            response_body = {}

        await save_idempotency_key(
            engine,
            idempotency_key,
            user_id,
            request_hash,
            response_body,
            self.time_provider.utc_now(),
        )

        return Response(
            content=raw_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
