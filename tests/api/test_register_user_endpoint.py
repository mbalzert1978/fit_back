"""Tests des HTTP-Randes von `POST /api/v1/identity/register`.

Geprueft wird ausschliesslich, was am Rand entsteht: Statuscodes, die
camelCase-Schreibweise, das RFC-7807-Format und die ISO-8601-Formatierung des
Zeitstempels. Das Verhalten des Use Case steht darunter und ist ueber die
Test-API schon abgedeckt; es hier ein zweites Mal zu pruefen wuerde nur
denselben Fall teurer wiederholen.

Die App wird aus Router und Exception-Handlern gebaut, nicht aus `main.py`
importiert: dessen Rate-Limit- und CSRF-Middleware gehoeren zu Ticket 0001, sind
prozessweit konfiguriert und haetten hier nur die Wirkung, den Rand hinter
Zufaellen zu verstecken.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.api.exception_handlers import register_exception_handlers
from src.api.identity import register_user_router

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
        await connection.execute(text("TRUNCATE identity.users"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(register_user_router)
    app.state.engine = postgres_engine

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http

    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))


async def test_legt_ein_konto_an(client: AsyncClient) -> None:
    """201 mit camelCase-Feldern und ISO-8601-Zeitstempel."""
    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "markus@example.de"
    assert body["displayName"] == "Markus"
    assert body["locale"] == "de"
    assert body["timeZoneId"] == "Europe/Berlin"
    assert body["userId"]
    # ISO-8601 mit Zeitzone - Unix-Sekunden bleiben drinnen.
    assert body["registeredAt"].endswith("+00:00")


async def test_die_transaktion_wird_committet(
    client: AsyncClient, postgres_engine: AsyncEngine
) -> None:
    """Nach der Antwort stehen Nutzer und Ereignis wirklich in der Datenbank."""
    await client.post("/api/v1/identity/register", json=_VALID_BODY)

    async with postgres_engine.begin() as connection:
        users = await connection.scalar(text("SELECT count(*) FROM identity.users"))
        events = await connection.scalar(text("SELECT count(*) FROM shared_kernel.outbox"))
    assert (users, events) == (1, 1)


async def test_vergebene_adresse_wird_zu_409(client: AsyncClient) -> None:
    """Zweite Registrierung derselben Adresse: 409 als problem+json."""
    await client.post("/api/v1/identity/register", json=_VALID_BODY)

    response = await client.post("/api/v1/identity/register", json=_VALID_BODY)

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["type"].endswith("/email-already-registered")
    assert problem["status"] == 409
    assert problem["instance"] == "/api/v1/identity/register"


async def test_ungueltige_eingabe_wird_zu_400_mit_feldfehlern(client: AsyncClient) -> None:
    """400 als problem+json, Feldnamen in der Schreibweise der Schnittstelle."""
    response = await client.post(
        "/api/v1/identity/register",
        json={**_VALID_BODY, "password": "kurz", "locale": "fr"},
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["type"].endswith("/validation-failed")
    assert set(problem["errors"]) == {"password", "locale"}


async def test_fehlendes_feld_wird_zu_400(client: AsyncClient) -> None:
    """Auch der Formfehler kommt als problem+json mit 400, nicht als 422.

    Zwei Ebenen, ein Format: Pydantic entscheidet ueber die Gestalt des Body,
    die Regeln des Slice ueber dessen Inhalt - der Aufrufer sieht in beiden
    Faellen dieselbe Fehlerstruktur.
    """
    incomplete = {key: value for key, value in _VALID_BODY.items() if key != "displayName"}

    response = await client.post("/api/v1/identity/register", json=incomplete)

    assert response.status_code == 400
    assert "displayName" in response.json()["errors"]
