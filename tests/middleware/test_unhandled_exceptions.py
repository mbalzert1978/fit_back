"""Tests des letzten Auffangpunkts fuer unbehandelte Ausnahmen.

Zwei Zusagen, und die zweite ist die wichtigere: der Fehler steht vollstaendig
im Log, und **nichts davon** steht in der Antwort.
"""

import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.middleware.unhandled_exceptions import (
    UNHANDLED_ERROR_TYPE,
    UnhandledExceptionMiddleware,
)

pytestmark = pytest.mark.asyncio

_GEHEIMNIS = "geheimer-verbindungsstring"


def _app_die_fliegt() -> FastAPI:
    """Eine App, deren Endpunkt eine Ausnahme mit verraeterischem Text wirft."""
    app = FastAPI()

    @app.get("/kaputt")
    async def kaputt() -> dict[str, str]:
        raise RuntimeError(f"Verbindung fehlgeschlagen: {_GEHEIMNIS}")

    @app.get("/heil")
    async def heil() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(UnhandledExceptionMiddleware)
    return app


async def test_eine_unbehandelte_ausnahme_wird_zu_500_als_problem_json() -> None:
    """Der Aufrufer bekommt ueberall dasselbe Format - auch im schlimmsten Fall."""
    transport = ASGITransport(app=_app_die_fliegt())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/kaputt")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["type"] == UNHANDLED_ERROR_TYPE
    assert problem["status"] == 500
    assert problem["instance"] == "/kaputt"


async def test_die_antwort_verraet_nichts_ueber_den_fehler() -> None:
    """Kein Stacktrace, kein Ausnahmetext, kein Dateipfad - das ist ein Informationsleck."""
    transport = ASGITransport(app=_app_die_fliegt())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/kaputt")

    body = response.text
    assert _GEHEIMNIS not in body
    assert "RuntimeError" not in body
    assert "Traceback" not in body


async def test_der_fehler_steht_mit_stacktrace_im_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ohne Stacktrace ist der Log-Eintrag zur Diagnose wertlos."""
    transport = ASGITransport(app=_app_die_fliegt())
    with caplog.at_level(logging.ERROR, logger="src.middleware.unhandled_exceptions"):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/kaputt")

    record = next(r for r in caplog.records if r.name == "src.middleware.unhandled_exceptions")
    assert record.levelno == logging.ERROR
    assert record.exc_info is not None
    assert "GET" in record.getMessage()
    assert "/kaputt" in record.getMessage()
    assert _GEHEIMNIS in caplog.text


async def test_eine_heile_anfrage_geht_unveraendert_durch() -> None:
    """Die Middleware ist ein Auffangpunkt, kein Umweg."""
    transport = ASGITransport(app=_app_die_fliegt())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/heil")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
