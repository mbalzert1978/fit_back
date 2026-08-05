"""Idempotency-Key middleware for POST/PUT deduplication.

Implements RFC 7231 idempotency via Idempotency-Key header.
Stores (key, user_id, request_hash, response_body, created_utc) in shared_kernel.idempotency_keys.
"""

import hashlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, final
from uuid import UUID

import asyncpg
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
IDEMPOTENCY_KEYS_TABLE = "shared_kernel.idempotency_keys"
IDEMPOTENT_METHODS = frozenset({"POST", "PUT"})
CACHEABLE_STATUS_CODES = frozenset({200, 201})

SELECT_IDEMPOTENCY_KEY_SQL = f"""SELECT key, user_id, request_hash, response_body, created_utc
    FROM {IDEMPOTENCY_KEYS_TABLE}
    WHERE key = $1 AND user_id = $2"""

INSERT_IDEMPOTENCY_KEY_SQL = f"""INSERT INTO {IDEMPOTENCY_KEYS_TABLE}
    (key, user_id, request_hash, response_body, created_utc)
    VALUES ($1, $2, $3, $4, $5)"""


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
    pool: asyncpg.Pool, key: UUID, user_id: UUID
) -> dict[str, Any] | None:
    """Hole einen Idempotency-Key aus der Datenbank.

    Args:
        pool: Datenbank-Verbindungspool
        key: UUID des Idempotency-Keys
        user_id: UUID des Benutzers

    Returns:
        Dict mit Key-Daten oder None, falls nicht vorhanden
    """
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                SELECT_IDEMPOTENCY_KEY_SQL,
                key,
                user_id,
            )
            if row:
                return dict(row)
            return None
    except Exception as e:  # noqa: BLE001 -- catch-all for DB connection issues
        logger.warning(f"Error fetching idempotency key: {e}")
        return None


async def save_idempotency_key(
    pool: asyncpg.Pool,
    key: UUID,
    user_id: UUID,
    request_hash: str,
    response_body: dict[str, Any],
) -> bool:
    """Speichere einen neuen Idempotency-Key in der Datenbank.

    Args:
        pool: Datenbank-Verbindungspool
        key: UUID des Idempotency-Keys
        user_id: UUID des Benutzers
        request_hash: SHA256-Hash des Requests
        response_body: Response-Body als Dict

    Returns:
        True, falls erfolgreich, False bei Fehler
    """
    try:
        async with pool.acquire() as conn:
            created_utc = datetime.now(tz=UTC)
            await conn.execute(
                INSERT_IDEMPOTENCY_KEY_SQL,
                key,
                user_id,
                request_hash,
                json.dumps(response_body),
                created_utc,
            )
        return True
    except Exception as e:  # noqa: BLE001 -- catch-all for DB write issues
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
        db_pool: asyncpg.Pool | None = None,
        time_provider: object | None = None,
        ttl_days: int = 7,
    ) -> None:
        """Initialisiere die Middleware.

        Args:
            app: Die ASGI-App
            db_pool: asyncpg-Verbindungspool (optional, wird sonst aus app.state geholt)
            time_provider: TimeProvider für deterministische Tests (nicht direkt genutzt)
            ttl_days: TTL in Tagen (Standard: 7)
        """
        super().__init__(app)
        self.db_pool = db_pool
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
        if is_idempotent_method(request.method):
            try:
                body_bytes = await request.body()
                body_str = body_bytes.decode("utf-8")
            except (UnicodeDecodeError, OSError) as e:
                logger.warning(f"Error reading request body: {e}")

        request_hash = calculate_request_hash(request.method, request.url.path, body_str)

        # Hole DB-Pool aus Constructor oder App-State
        pool = self.db_pool or getattr(request.app.state, "db_pool", None)
        if not pool:
            logger.warning("No database pool available, skipping idempotency check")
            return await call_next(request)

        # Prüfe, ob Key bekannt ist
        existing_key = await get_idempotency_key_from_db(pool, idempotency_key, user_id)
        if existing_key:
            logger.info(f"Idempotency key {idempotency_key} found, returning cached response")
            response_body = existing_key.get("response_body")
            return JSONResponse(
                content=response_body,
                status_code=200,
            )

        # Key ist neu: verarbeite Request normal
        response = await call_next(request)

        # Speichere Response in Datenbank (nur für erfolgreiche Responses 201, 200)
        if response.status_code in CACHEABLE_STATUS_CODES:
            try:
                response_body = json.loads(response.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
                logger.warning(f"Error parsing response body: {e}")
                response_body = {}

            await save_idempotency_key(
                pool,
                idempotency_key,
                user_id,
                request_hash,
                response_body,
            )

        return response
