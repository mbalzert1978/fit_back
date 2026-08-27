"""Smoke-Test des Anwendungs-Einstiegspunkts.

Klein, aber die Luecken, die er schliesst, waren teuer. Zweimal hintereinander
war `src/main.py` ueber mehrere Tickets hinweg kaputt, ohne dass die CI etwas
gemerkt haette:

1. Das Modul liess sich **nicht importieren** - zwei Importe zeigten auf Module,
   die es nicht gibt (`fastapi.middleware.base`, `starlette.middleware.csrf`).
   Sie kamen aus einem Commit, der zurueckgenommen wurde, und ueber den Merge
   eines aelteren Branches unbemerkt zurueck.
2. Der Startup brach ab, weil der Lifespan `add_middleware` aufrief - zu spaet,
   Starlette hat die Kette da schon gebaut. Siehe
   `docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`.

Fuer den zweiten Fehler reichte ein Import-Test nicht: er war erst sichtbar,
wenn der Lifespan wirklich laeuft. Deshalb faehrt dieser Test ihn ueber das rohe
ASGI-Protokoll - genau dieser Aufruf ist es, der die Middleware-Kette baut.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from testcontainers.community.postgres import PostgresContainer


def test_der_einstiegspunkt_laesst_sich_importieren() -> None:
    """`from src import main` darf keine Umgebungsvariablen und keine Datenbank brauchen.

    Die Konfiguration wird erst beim Start geprueft (`lifespan`), nicht beim
    Import - sonst waere jedes Werkzeug, das das Modul nur laden will, an eine
    vollstaendige Umgebung gebunden.
    """
    from src import main

    assert main.app.title == "Fit-back API"


@pytest.mark.parametrize("path", ["/api/v1/health", "/api/v1/identity/register"])
def test_die_anwendung_kennt_ihre_endpunkte(path: str) -> None:
    """Gegen das OpenAPI-Schema geprueft, nicht gegen `app.routes`.

    FastAPI haengt eingebundene Router als Referenz ein, statt ihre Routen
    flachzuziehen; das Schema ist die verlaessliche Aufzaehlung.
    """
    from src import main

    assert path in main.app.openapi()["paths"]


async def _run_lifespan(app: FastAPI, message: str) -> dict[str, Any]:
    """Bewusst das rohe ASGI-Protokoll statt eines Test-Clients: nur dieser Weg
    baut die Middleware-Kette so auf, wie uvicorn es tut.
    """
    answers: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": message}

    async def send(event: dict[str, Any]) -> None:
        answers.append(event)

    await app({"type": "lifespan", "asgi": {"version": "3.0"}}, receive, send)
    return answers[0]


@pytest_asyncio.fixture
async def gestartete_app(
    postgres_service: PostgresContainer, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[FastAPI]:
    """Fahre die echte App gegen die Testdatenbank hoch und wieder herunter."""
    monkeypatch.setenv("DB_HOST", postgres_service.get_container_host_ip())
    monkeypatch.setenv("DB_PORT", str(postgres_service.get_exposed_port(5432)))
    monkeypatch.setenv("DB_NAME", "test")
    monkeypatch.setenv("DB_USER", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")
    monkeypatch.setenv("JWT_SECRET", "test-geheimnis-mit-mindestens-32-zeichen")

    from src import main

    startup = await _run_lifespan(main.app, "lifespan.startup")
    assert startup["type"] == "lifespan.startup.complete", startup.get("message")

    yield main.app

    await _run_lifespan(main.app, "lifespan.shutdown")


@pytest.mark.asyncio
async def test_der_startup_laeuft_durch(gestartete_app: FastAPI) -> None:
    """Regression: der Lifespan kam nie bis zum `yield`.

    Er rief `add_middleware` auf, was Starlette mit "Cannot add middleware after
    an application has started" quittiert - die Anwendung war nicht startfaehig.
    """
    assert gestartete_app.state.engine is not None


@pytest.mark.asyncio
async def test_der_health_endpunkt_antwortet_gegen_die_echte_datenbank(
    gestartete_app: FastAPI,
) -> None:
    """Der Health-Check laeuft ueber dieselbe Engine wie die Slices - es gibt nur die eine."""
    transport = ASGITransport(app=gestartete_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    # Der `{data, meta}`-Umschlag gilt fuer den ganzen Host, nicht nur fuer
    # Identity (`src/middleware/response_envelope.py`) - auch der Health-Check
    # antwortet darin.
    assert response.json()["data"] == {"status": "healthy"}
