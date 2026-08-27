"""Welche Pydantic-Fehlertypen am Exception-Handler ankommen koennen.

`_fault_of` in `src/api/exception_handlers.py` zaehlt diese Typen auf und schliesst mit
`assert_never`. Die Aufzaehlung ist nur so lange richtig, wie das installierte Pydantic
und FastAPI sich daran halten - darauf haben wir keinen Einfluss.

Deshalb wird sie nicht behauptet, sondern **gemessen**, und zwar durch den echten
Endpunkt statt gegen das Modell allein. Das ist nicht dasselbe: FastAPI legt eine eigene
Validierungsschicht um den Body, und ein JSON-Array meldet dort `model_attributes_type`,
waehrend `RegisterUserBody.model_validate([])` `model_type` liefert. Wer nur das Modell
faehrt, misst einen Vertrag, den der Handler nie sieht - dieser Test hat genau diesen
Fehler zuerst gemacht.

Aendert ein Update daran etwas, wird der Test rot: in der CI, vor dem Deployment, statt
zur Laufzeit bei einem Aufrufer. Die andere Haelfte prueft `verify_pydantic_contract`
beim Start - dort geht es um die Existenz der Typen, hier um ihr Verhalten.

Regel: `.rules/python/python-error-handling.md`, "Jeder `match` ist vollstaendig".
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, field_validator

from src.api.exception_handlers import HANDLED_PYDANTIC_ERROR_TYPES
from src.api.identity import register_user_router
from src.api.identity.dependencies import _register_user

pytestmark = pytest.mark.asyncio

GUELTIG = {
    "email": "jemand@example.com",
    "password": "ein-langes-passwort",
    "displayName": "Jemand",
    "locale": "de",
    "timeZoneId": "Europe/Berlin",
}

KAPUTTE_EINGABEN: dict[str, object] = {
    "leerer Body": {},
    "Pflichtfeld fehlt": {k: v for k, v in GUELTIG.items() if k != "email"},
    "unbekanntes Feld": GUELTIG | {"unbekannt": 1},
    "dict statt Text": GUELTIG | {"email": {}},
    "Zahl statt Text": GUELTIG | {"email": 5},
    "null statt Text": GUELTIG | {"email": None},
    "Liste statt Text": GUELTIG | {"email": []},
    "bool statt Text": GUELTIG | {"email": True},
    "Array statt Objekt": [],
    "Text statt Objekt": "nur ein string",
    "Zahl statt Objekt": 42,
}
"""Eingaben, die als gueltiges JSON ankommen, aber die Validierung nicht bestehen."""

KAPUTTES_JSON = {"unparsbar": "{nicht json", "abgeschnitten": '{"email": '}
"""Eingaben, die gar nicht erst als JSON durchgehen."""


class _ModellMitValidator(BaseModel):
    """Stellvertreter fuer jedes Modell mit eigenem `field_validator`.

    `RegisterUserBody` hat bewusst keinen - fachliche Pruefung gehoert in den Slice.
    Der Exception-Handler haengt aber app-weit und sieht jedes Modell, also gehoert
    `value_error` zur gemessenen Menge. Ohne diesen Stellvertreter faende der Test den
    Typ nicht und hielte den zugehoerigen Zweig faelschlich fuer tot.
    """

    wert: str

    @field_validator("wert")
    @classmethod
    def _wert_wird_abgelehnt(cls, _wert: str) -> str:
        msg = "abgelehnt"
        raise ValueError(msg)


@pytest_asyncio.fixture
async def messender_client() -> AsyncGenerator[tuple[AsyncClient, set[str]]]:
    """Eine App, die die **rohen** Pydantic-Fehlertypen mitschreibt.

    Bewusst nicht der echte Handler: der bildet die Typen ja gerade auf unsere Faelle ab
    und verschluckt damit, was gemessen werden soll. Registriert wird stattdessen ein
    Mitschreiber auf derselben Ausnahme, ueber dieselbe Router-Verdrahtung.
    """
    gesehen: set[str] = set()

    app = FastAPI()
    app.include_router(register_user_router)

    # Die Pipeline wird nie aufgerufen - jede Eingabe hier scheitert vorher an der
    # Validierung. Sie muss sich aber aufloesen lassen, sonst kaeme FastAPI gar nicht
    # bis zur Validierung. Kein Fake, sondern schlicht nichts: wird sie doch benutzt,
    # soll der Test daran scheitern und nicht stillschweigend etwas anderes messen.
    app.dependency_overrides[_register_user] = lambda: None

    @app.post("/mit-validator")
    async def _mit_validator(body: _ModellMitValidator) -> dict[str, str]:
        return {"wert": body.wert}

    # Starlettes Handler-Signatur ist auf `Exception` festgelegt und nicht auf die
    # registrierte Ausnahme; die Einengung holt der Mitschreiber selbst nach.
    async def _mitschreiben(_: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RequestValidationError)
        gesehen.update(fehler["type"] for fehler in exc.errors())
        return JSONResponse(status_code=400, content={})

    app.add_exception_handler(RequestValidationError, _mitschreiben)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http, gesehen


async def _alle_erreichbaren_fehlertypen(client: AsyncClient, gesehen: set[str]) -> set[str]:
    """Fahre jede Form kaputter Eingabe durch den echten Endpunkt."""
    pfad = "/api/v1/identity/register"
    for eingabe in KAPUTTE_EINGABEN.values():
        await client.post(pfad, json=eingabe)
    for roh in KAPUTTES_JSON.values():
        await client.post(pfad, content=roh, headers={"Content-Type": "application/json"})
    await client.post("/mit-validator", json={"wert": "egal"})
    return gesehen


async def test_kein_erreichbarer_fehlertyp_ist_unbehandelt(
    messender_client: tuple[AsyncClient, set[str]],
) -> None:
    """Ein Typ, den der Endpunkt erzeugt, aber `_fault_of` nicht kennt, ergaebe HTTP 500."""
    client, gesehen = messender_client
    erreichbar = await _alle_erreichbaren_fehlertypen(client, gesehen)
    unbehandelt = sorted(erreichbar - HANDLED_PYDANTIC_ERROR_TYPES)

    assert not unbehandelt, (
        f"Der Endpunkt erzeugt diese Pydantic-Fehlertypen, die `_fault_of` nicht behandelt: "
        f"{unbehandelt}. Sie laufen dort in `assert_never`, und der Aufrufer bekaeme HTTP 500 "
        "statt einer uebersetzten 400. Je Typ einen eigenen Fall in "
        "src/api/request_validation_errors.py anlegen, in `_fault_of` abbilden, den Text in "
        "beide Sprachdateien schreiben und den Typ in HANDLED_PYDANTIC_ERROR_TYPES aufnehmen."
    )


async def test_kein_behandelter_fehlertyp_ist_unerreichbar(
    messender_client: tuple[AsyncClient, set[str]],
) -> None:
    """Ein Fall, den nichts mehr ausloest, ist toter Code samt toter Textvorlage."""
    client, gesehen = messender_client
    erreichbar = await _alle_erreichbaren_fehlertypen(client, gesehen)
    unerreichbar = sorted(HANDLED_PYDANTIC_ERROR_TYPES - erreichbar)

    assert not unerreichbar, (
        f"`_fault_of` behandelt diese Fehlertypen, aber keine Eingabe loest sie noch aus: "
        f"{unerreichbar}. Entweder fehlt oben eine Form kaputter Eingabe, die sie ausloest, "
        "oder Pydantic meldet sie nicht mehr und der Zweig samt Textvorlage gehoert weg."
    )


@pytest.mark.parametrize("bezeichnung", sorted(KAPUTTE_EINGABEN))
async def test_jede_kaputte_eingabe_wird_abgelehnt(
    bezeichnung: str, messender_client: tuple[AsyncClient, set[str]]
) -> None:
    """Eine Eingabe, die stillschweigend durchginge, verfaelschte die Messung oben."""
    client, _ = messender_client
    antwort = await client.post("/api/v1/identity/register", json=KAPUTTE_EINGABEN[bezeichnung])

    assert antwort.status_code == 400
