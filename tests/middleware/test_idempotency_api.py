"""Integrationstests der Idempotency-Key-Middleware gegen eine echte Datenbank.

Diese Datei lief bisher gegen eine `db_pool`-Fixture, die `None` zurueckgab -
der eine Test, auf den es ankommt (zweiter Aufruf mit demselben Schluessel
liefert die gespeicherte Antwort), hat sich damit selbst uebersprungen. Er laeuft
jetzt gegen die Testcontainers-Engine, dieselbe, die auch die Slices benutzen.
"""

from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.contexts.shared_kernel.time_provider import FakeTimeProvider
from src.middleware.idempotency import IdempotencyKeyMiddleware

pytestmark = pytest.mark.asyncio


class _StubAuthMiddleware(BaseHTTPMiddleware):
    """Setzt eine feste `user_id` - die Idempotenz haengt an ihr."""

    def __init__(self, app: object, user_id: UUID) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._user_id = user_id

    async def dispatch(self, request: Request, call_next: object) -> Response:
        request.state.user_id = self._user_id
        return await call_next(request)  # type: ignore[operator]


def _build_app(engine: AsyncEngine, user_id: UUID | None) -> FastAPI:
    """Baue eine App mit einem Dummy-Endpunkt hinter der Middleware.

    `user_id=None` laesst die Stub-Auth weg und bildet damit den
    unauthentifizierten Fall ab.

    Reihenfolge: `add_middleware` schiebt jeweils nach vorn, die zuletzt
    hinzugefuegte Middleware laeuft also **aussen**. Die Auth muss aussen
    liegen, sonst sieht die Idempotenz-Pruefung noch keine `user_id`.
    """
    app = FastAPI()

    @app.post("/api/v1/test-idempotency")
    async def create() -> JSONResponse:
        return JSONResponse(status_code=201, content={"id": str(uuid4()), "data": "angelegt"})

    @app.put("/api/v1/test-idempotency")
    async def update() -> JSONResponse:
        return JSONResponse(status_code=200, content={"updated": True})

    @app.get("/api/v1/test-idempotency")
    async def read() -> JSONResponse:
        return JSONResponse(status_code=200, content={"data": "gelesen"})

    app.add_middleware(IdempotencyKeyMiddleware, time_provider=FakeTimeProvider())
    if user_id is not None:
        app.add_middleware(_StubAuthMiddleware, user_id=user_id)
    app.state.engine = engine
    return app


@pytest_asyncio.fixture
async def clean_idempotency_keys(postgres_engine: AsyncEngine) -> AsyncGenerator[AsyncEngine]:
    """Leere die Tabelle vor und nach jedem Test."""
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE shared_kernel.idempotency_keys"))
    yield postgres_engine
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE shared_kernel.idempotency_keys"))


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_zweiter_aufruf_liefert_die_gespeicherte_antwort(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Der Kern des Tickets: gleicher Schluessel, gleiche Antwort, jetzt mit 200."""
    app = _build_app(clean_idempotency_keys, user_id=uuid4())
    key = str(uuid4())

    async with await _client(app) as client:
        first = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})
        second = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()


async def test_der_eintrag_traegt_alle_geforderten_felder(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """`shared_kernel.idempotency_keys` bekommt Schluessel, Nutzer, Hash, Body und Zeitpunkt."""
    user_id = uuid4()
    app = _build_app(clean_idempotency_keys, user_id=user_id)
    key = uuid4()

    async with await _client(app) as client:
        await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": str(key)})

    async with clean_idempotency_keys.connect() as connection:
        found = await connection.execute(
            text("""
                SELECT key, user_id, request_hash, response_body, created_utc
                FROM shared_kernel.idempotency_keys
            """)
        )
        row = found.mappings().one()

    assert row["key"] == key
    assert row["user_id"] == user_id
    assert len(row["request_hash"]) == 64
    assert "angelegt" in row["response_body"]
    # FakeTimeProvider steht auf 2000-01-01 - der Zeitpunkt kommt aus dem
    # TimeProvider, nicht aus einem direkten Uhrablesen in der Middleware.
    assert row["created_utc"].year == 2000


async def test_verschiedene_schluessel_stoeren_sich_nicht(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Zwei Schluessel, zwei Vorgaenge - kein Treffer im Zwischenspeicher."""
    app = _build_app(clean_idempotency_keys, user_id=uuid4())

    async with await _client(app) as client:
        first = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(uuid4())}
        )
        second = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(uuid4())}
        )

    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json() != second.json()


async def test_ohne_schluessel_geht_die_anfrage_durch(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Ohne Header greift die Middleware nicht ein."""
    app = _build_app(clean_idempotency_keys, user_id=uuid4())

    async with await _client(app) as client:
        response = await client.post("/api/v1/test-idempotency")

    assert response.status_code == 201


async def test_ohne_angemeldeten_nutzer_geht_die_anfrage_durch(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Idempotenz haengt an der `user_id`; ohne sie wird nichts gespeichert."""
    app = _build_app(clean_idempotency_keys, user_id=None)
    key = str(uuid4())

    async with await _client(app) as client:
        first = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})
        second = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    assert (first.status_code, second.status_code) == (201, 201)

    async with clean_idempotency_keys.connect() as connection:
        stored = await connection.scalar(
            text("SELECT count(*) FROM shared_kernel.idempotency_keys")
        )
    assert stored == 0


async def test_ungueltige_uuid_im_header_geht_durch(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Ein unlesbarer Schluessel bricht die Anfrage nicht ab."""
    app = _build_app(clean_idempotency_keys, user_id=uuid4())

    async with await _client(app) as client:
        response = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": "kein-uuid"}
        )

    assert response.status_code == 201


async def test_get_wird_nicht_behandelt(clean_idempotency_keys: AsyncEngine) -> None:
    """Nur POST und PUT sind idempotenzpflichtig."""
    app = _build_app(clean_idempotency_keys, user_id=uuid4())

    async with await _client(app) as client:
        response = await client.get(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(uuid4())}
        )

    assert response.status_code == 200


async def test_put_wird_ebenfalls_zwischengespeichert(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """PUT faellt unter dieselbe Regel wie POST."""
    app = _build_app(clean_idempotency_keys, user_id=uuid4())
    key = str(uuid4())

    async with await _client(app) as client:
        await client.put("/api/v1/test-idempotency", headers={"Idempotency-Key": key})
        second = await client.put("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    assert second.status_code == 200
    async with clean_idempotency_keys.connect() as connection:
        stored = await connection.scalar(
            text("SELECT count(*) FROM shared_kernel.idempotency_keys")
        )
    assert stored == 1
