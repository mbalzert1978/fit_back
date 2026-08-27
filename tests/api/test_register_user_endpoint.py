"""Tests des HTTP-Randes von `POST /api/v1/identity/register`.

Geprueft wird ausschliesslich, was am Rand entsteht: Statuscodes, die
camelCase-Schreibweise, der `{data, meta}`-Umschlag, die Kopfzeilen der 201 und
das RFC-7807-Format. Das Verhalten des Use Case steht darunter und ist ueber die
Test-API schon abgedeckt; es hier ein zweites Mal zu pruefen wuerde nur
denselben Fall teurer wiederholen.

Was der Vertrag des Frontends verlangt, prueft nicht dieser Test, sondern der
Provider-Lauf in `tests/contracts/` - er spielt die Interaktionen des Pacts ab.
Hier steht, was dieser Rand daraus macht.

Die App wird aus Router und Exception-Handlern gebaut, nicht aus `main.py`
importiert: dessen Rate-Limit- und CSRF-Middleware gehoeren zu Ticket 0001, sind
prozessweit konfiguriert und haetten hier nur die Wirkung, den Rand hinter
Zufaellen zu verstecken.
"""

import hashlib
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.api.exception_handlers import register_exception_handlers
from src.api.i18n import create_resources
from src.api.identity import register_user_router
from src.contexts.shared_kernel.time_provider import SystemTimeProvider
from src.middleware.response_envelope import ResponseEnvelopeMiddleware
from src.settings import DEFAULT_API_VERSION, Settings, get_settings

pytestmark = pytest.mark.asyncio

_VALID_BODY = {
    "email": "markus@example.de",
    "password": "ein-langes-passwort",
    "displayName": "Markus",
    "locale": "de",
    "timeZoneId": "Europe/Berlin",
}


@pytest_asyncio.fixture
async def client(postgres_engine: AsyncEngine) -> AsyncGenerator[AsyncClient]:
    """Baue die App um den Router und leere die betroffenen Tabellen."""
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users CASCADE"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))

    app = FastAPI()
    app.state.resources = create_resources()
    # Dieselbe Konfiguration, die der Lifespan sonst prueft: der Slice signiert
    # seine Access-Token damit. Ueberschrieben statt in die Umgebung gelegt -
    # der dokumentierte Weg, eine Settings-Dependency im Test zu tauschen.
    settings = Settings(db_password="test", jwt_secret="t" * 32)
    app.dependency_overrides[get_settings] = lambda: settings
    # Der Umschlag gehoert zum Host und nicht zum Router - wer den Rand misst,
    # misst ihn mit.
    app.add_middleware(
        ResponseEnvelopeMiddleware,
        time_provider=SystemTimeProvider(),
        api_version=DEFAULT_API_VERSION,
    )
    register_exception_handlers(app)
    app.include_router(register_user_router)
    app.state.engine = postgres_engine

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http

    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users CASCADE"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))


async def test_legt_ein_konto_an(client: AsyncClient) -> None:
    """201 mit dem angelegten Konto unter `data.user`."""
    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)

    assert response.status_code == 201
    user = response.json()["data"]["user"]
    assert user["email"] == "markus@example.de"
    assert user["displayName"] == "Markus"
    assert user["locale"] == "de"
    assert user["timeZoneId"] == "Europe/Berlin"
    assert user["id"]


async def test_die_201_gibt_eine_sitzung_heraus(client: AsyncClient) -> None:
    """Wer sich registriert, ist angemeldet - beide Token kommen mit."""
    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)

    session = response.json()["data"]["session"]
    assert session["tokenType"] == "Bearer"
    assert session["accessToken"]
    assert session["refreshToken"]
    assert session["expiresIn"] > 0
    assert session["refreshExpiresIn"] > session["expiresIn"]


async def test_der_umschlag_und_die_kopfzeilen_der_201(client: AsyncClient) -> None:
    """`meta`, `Location`, `X-Request-Id` und `Cache-Control` kommen aus der Middleware."""
    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)

    meta = response.json()["meta"]
    assert meta["apiVersion"] == "1"
    assert meta["requestId"] == response.headers["X-Request-Id"]
    assert meta["timestamp"].endswith("Z")
    assert response.headers["Location"] == "/api/v1/identity/me"
    assert response.headers["Cache-Control"] == "no-store"


async def test_der_ausgegebene_refresh_token_ist_abgelegt(
    client: AsyncClient, postgres_engine: AsyncEngine
) -> None:
    """Ein Refresh-Token, den niemand einloesen kann, waere eine Luege.

    Verglichen wird gegen den **Hash**: der Klartext steht nicht in der
    Datenbank, und genau das ist die Zusage
    (`src/contexts/identity/infrastructure/tokens/postgres_session_tokens.py`).
    """
    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)
    ausgegeben = response.json()["data"]["session"]["refreshToken"]

    async with postgres_engine.begin() as connection:
        abgelegt = await connection.scalar(text("SELECT token_hash FROM identity.refresh_tokens"))

    assert abgelegt == hashlib.sha256(ausgegeben.encode()).hexdigest()


async def test_die_transaktion_wird_committet(
    client: AsyncClient, postgres_engine: AsyncEngine
) -> None:
    await client.post("/api/v1/identity/register", json=_VALID_BODY)

    async with postgres_engine.begin() as connection:
        users = await connection.scalar(text("SELECT count(*) FROM identity.users"))
        events = await connection.scalar(text("SELECT count(*) FROM shared_kernel.outbox"))
        tokens = await connection.scalar(text("SELECT count(*) FROM identity.refresh_tokens"))
    assert (users, events, tokens) == (1, 1, 1)


async def test_vergebene_adresse_wird_zu_409(client: AsyncClient) -> None:
    await client.post("/api/v1/identity/register", json=_VALID_BODY)

    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["type"].endswith("/email-already-registered")
    assert problem["status"] == 409
    assert problem["instance"] == "/api/v1/identity/register"


async def test_ein_abgelehnter_versuch_traegt_kein_location(client: AsyncClient) -> None:
    """`Location` gehoert zur 201 und nur zu ihr.

    Geprueft wird die Leitung, nicht der Zweig im Endpunkt: ein `Location` auf
    dem 409 zeigte auf ein Konto, das dieser Aufruf nicht angelegt hat.

    Die Kopfzeilen der 201 kommen aus einer Dependency, und eine Dependency
    laeuft vor dem Endpunkt - also auch vor einer Ablehnung. Dass der Endpunkt
    sie trotzdem erst im 201-Zweig setzt, faengt dieser Test **nicht**: FastAPI
    verwirft die Kopfzeilen der eingespritzten `Response`, sobald ein Endpunkt
    selbst eine `Response` zurueckgibt. Der Zweig steht dort aus einem anderen
    Grund - siehe `_created_headers` in `register_user_response.py`.
    """
    await client.post("/api/v1/identity/register", json=_VALID_BODY)

    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)

    assert response.status_code == 409
    assert "location" not in response.headers


async def test_ungueltige_eingabe_wird_zu_422_mit_feldfehlern(client: AsyncClient) -> None:
    """422 als problem+json, Feldnamen in der Schreibweise der Schnittstelle."""
    response = await client.post(
        "/api/v1/identity/register",
        json={**_VALID_BODY, "password": "kurz", "locale": "fr"},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["type"].endswith("/validation-failed")
    assert set(problem["errors"]) == {"password", "locale"}


async def test_fehlendes_feld_wird_zu_422(client: AsyncClient) -> None:
    """Auch der Formfehler kommt als problem+json - dieselbe Struktur, derselbe Code.

    Zwei Ebenen, ein Format: Pydantic entscheidet ueber die Gestalt des Body,
    die Regeln des Slice ueber dessen Inhalt - der Aufrufer sieht in beiden
    Faellen dieselbe Fehlerstruktur.
    """
    incomplete = {key: value for key, value in _VALID_BODY.items() if key != "displayName"}

    response = await client.post("/api/v1/identity/register", json=incomplete)

    assert response.status_code == 422
    assert "displayName" in response.json()["errors"]


async def test_kein_fehlerkoerper_traegt_den_umschlag(client: AsyncClient) -> None:
    """4xx ist nacktes `problem+json`: der Umschlag gilt nur fuer 2xx.

    Ein eingepacktes Problem waere ein zweites Fehlerformat neben RFC 7807 -
    und der Vertrag des Frontends kennt nur eines.
    """
    response = await client.post(
        "/api/v1/identity/register",
        json={**_VALID_BODY, "password": "kurz"},
    )

    body = response.json()
    assert "data" not in body
    assert "meta" not in body
    assert body["type"].startswith("tag:nutritrack.app,2026:problems/")
    # Die Kennung geht trotzdem mit - genau die Antwort will man im Log wiederfinden.
    assert response.headers["X-Request-Id"]
