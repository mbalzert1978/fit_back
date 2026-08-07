"""Tests der i18n-Rendering am HTTP-Rand.

Geprueft wird, dass Accept-Language-Header die zweisprachigen Antworten
tatsaechlich beeinflussen und dass die HTTP-Raender korrekt zwischen
den Sprachen unterscheiden:
- title und detail werden uebersetzt
- Content-Language wird korrekt gesetzt
- type, status, code bleiben sprachenunabhaengig gleich
- errors.* wird bei Validierungsfehlern ebenfalls uebersetzt
"""

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
    app.state.resources = create_resources()
    register_exception_handlers(app)
    app.include_router(register_user_router)
    app.state.engine = postgres_engine

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http

    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))


class TestAcceptLanguageInfluencesResponse:
    """HTTP-Anfragen mit unterschiedlichen Accept-Language geben unterschiedliche Texte."""

    async def test_email_already_registered_auf_de(self, client: AsyncClient) -> None:
        """Accept-Language: de-DE liefert deutsche Texte."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "de-DE"},
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "de-DE"
        problem = response.json()
        assert "Diese E-Mail-Adresse ist bereits registriert" in problem["title"]
        assert "bereits mit einem anderen Konto" in problem["detail"]

    async def test_email_already_registered_auf_en(self, client: AsyncClient) -> None:
        """Accept-Language: en-US liefert englische Texte."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "en-US"},
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "en-US"
        problem = response.json()
        assert "already registered" in problem["title"]
        assert "already associated" in problem["detail"]

    async def test_type_und_status_sprachenunabhaengig(self, client: AsyncClient) -> None:
        """Sprachwahl aendert type und status nicht."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response_de = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "de-DE"},
        )
        response_en = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "en-US"},
        )

        problem_de = response_de.json()
        problem_en = response_en.json()

        assert problem_de["type"] == problem_en["type"]
        assert problem_de["status"] == problem_en["status"]
        # Fehlercode (extracted from type) bleibt gleich
        assert "email-already-registered" in problem_de["type"]
        assert "email-already-registered" in problem_en["type"]

    async def test_validation_failed_auf_de(self, client: AsyncClient) -> None:
        """Validierungsfehler werden auf Deutsch uebersetzt."""
        response = await client.post(
            "/api/v1/identity/register",
            json={**_VALID_BODY, "password": "kurz", "locale": "fr"},
            headers={"Accept-Language": "de-DE"},
        )

        assert response.status_code == 400
        assert response.headers["Content-Language"] == "de-DE"
        problem = response.json()
        assert "ungültig" in problem["title"]

    async def test_validation_failed_auf_en(self, client: AsyncClient) -> None:
        """Validierungsfehler werden auf Englisch uebersetzt."""
        response = await client.post(
            "/api/v1/identity/register",
            json={**_VALID_BODY, "password": "kurz", "locale": "fr"},
            headers={"Accept-Language": "en-US"},
        )

        assert response.status_code == 400
        assert response.headers["Content-Language"] == "en-US"
        problem = response.json()
        assert "invalid" in problem["title"]

    async def test_fehlender_header_faellt_auf_de_default(self, client: AsyncClient) -> None:
        """Ohne Accept-Language kommt de-DE (Standardsprache)."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            # kein Accept-Language-Header
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "de-DE"
        problem = response.json()
        assert "Diese E-Mail-Adresse ist bereits registriert" in problem["title"]

    async def test_unknown_language_faellt_auf_de_default(self, client: AsyncClient) -> None:
        """Unbekannte Sprache faellt auf de-DE zurueck."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "ja-JP"},
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "de-DE"
        problem = response.json()
        assert "Diese E-Mail-Adresse ist bereits registriert" in problem["title"]

    async def test_case_insensitive_matching(self, client: AsyncClient) -> None:
        """EN-us und en-US sind austauschbar."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "EN-US"},
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "en-US"
        problem = response.json()
        assert "already registered" in problem["title"]

    async def test_region_fallback_de_at_zu_de_de(self, client: AsyncClient) -> None:
        """de-AT faellt auf de-DE zurueck."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "de-AT"},
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "de-DE"
        problem = response.json()
        assert "Diese E-Mail-Adresse ist bereits registriert" in problem["title"]

    async def test_region_fallback_en_gb_zu_en_us(self, client: AsyncClient) -> None:
        """en-GB faellt auf en-US zurueck."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "en-GB"},
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "en-US"
        problem = response.json()
        assert "already registered" in problem["title"]

    async def test_q_weights_influence_choice(self, client: AsyncClient) -> None:
        """Q-Gewichte beeinflussen die Sprachwahl."""
        await client.post("/api/v1/identity/register", json=_VALID_BODY)

        # de;q=0.5,en-US;q=0.9 sollte en-US waehlen
        response = await client.post(
            "/api/v1/identity/register",
            json=_VALID_BODY,
            headers={"Accept-Language": "de;q=0.5,en-US;q=0.9"},
        )

        assert response.status_code == 409
        assert response.headers["Content-Language"] == "en-US"
        problem = response.json()
        assert "already registered" in problem["title"]


class TestStrukturelleRequestFehler:
    """Auch Pydantics eigene Befunde tragen unsere Codes - und beide Sprachen.

    Frueher reichte der Handler die Rohmeldung der Bibliothek durch: `title`/`detail`
    zweisprachig, die Feldfehler dieses Pfades aber immer englisch. Damit haette
    `errors.*` je nach Fehlerursache zwei verschiedene Vertraege getragen.
    """

    async def test_fehlendes_pflichtfeld_zweisprachig(self, client: AsyncClient) -> None:
        body = {key: value for key, value in _VALID_BODY.items() if key != "email"}

        auf_deutsch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "de-DE"}
        )
        auf_englisch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "en-US"}
        )

        assert auf_deutsch.status_code == 400
        assert auf_deutsch.json()["errors"]["email"] == ["Das Feld 'email' ist erforderlich"]
        assert auf_englisch.json()["errors"]["email"] == ["The field 'email' is required"]

    async def test_unbekanntes_feld_zweisprachig(self, client: AsyncClient) -> None:
        body = _VALID_BODY | {"schmuggelware": "x"}

        auf_deutsch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "de-DE"}
        )
        auf_englisch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "en-US"}
        )

        assert auf_deutsch.status_code == 400
        assert "schmuggelware" in auf_deutsch.json()["errors"]["schmuggelware"][0]
        assert (
            auf_deutsch.json()["errors"]["schmuggelware"]
            != (auf_englisch.json()["errors"]["schmuggelware"])
        )

    async def test_falscher_feldtyp_zweisprachig(self, client: AsyncClient) -> None:
        body = _VALID_BODY | {"displayName": {"kein": "text"}}

        auf_deutsch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "de-DE"}
        )
        auf_englisch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "en-US"}
        )

        assert auf_deutsch.status_code == 400
        assert auf_deutsch.json()["errors"]["displayName"] == [
            "Das Feld 'displayName' muss ein Text sein"
        ]
        assert auf_englisch.json()["errors"]["displayName"] == [
            "The field 'displayName' must be a string"
        ]

    async def test_kaputtes_json_zweisprachig(self, client: AsyncClient) -> None:
        kaputt = "{nicht wirklich json"

        auf_deutsch = await client.post(
            "/api/v1/identity/register",
            content=kaputt,
            headers={"Accept-Language": "de-DE", "Content-Type": "application/json"},
        )
        auf_englisch = await client.post(
            "/api/v1/identity/register",
            content=kaputt,
            headers={"Accept-Language": "en-US", "Content-Type": "application/json"},
        )

        assert auf_deutsch.status_code == 400
        assert auf_deutsch.json()["errors"]["body"] == ["Die Anfrage enthält ungültiges JSON"]
        assert auf_englisch.json()["errors"]["body"] == ["The request contains invalid JSON"]

    async def test_der_code_bleibt_sprachunabhaengig(self, client: AsyncClient) -> None:
        """Der `type` ist der Vertrag, der Text die Kosmetik darueber."""
        body = {key: value for key, value in _VALID_BODY.items() if key != "email"}

        auf_deutsch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "de-DE"}
        )
        auf_englisch = await client.post(
            "/api/v1/identity/register", json=body, headers={"Accept-Language": "en-US"}
        )

        assert auf_deutsch.json()["type"] == auf_englisch.json()["type"]
        assert auf_deutsch.json()["status"] == auf_englisch.json()["status"]
        assert auf_deutsch.json()["title"] != auf_englisch.json()["title"]
