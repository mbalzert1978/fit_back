"""Was der Antwort-Umschlag mit den Kopfzeilen macht, die er vorfindet.

Der Umschlag baut die Antwort neu auf - dabei koennen Kopfzeilen verlorengehen,
und zwar still. Diese Ebene prueft genau das; dass Identity-Antworten die
richtige Form haben, prueft `tests/api/test_register_user_endpoint.py`.
"""

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from httpx import ASGITransport, AsyncClient
from httpx import Response as HttpxResponse

from src.contexts.shared_kernel.time_provider import SystemTimeProvider
from src.middleware.response_envelope import ResponseEnvelopeMiddleware
from src.settings import DEFAULT_API_VERSION

pytestmark = pytest.mark.asyncio


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        ResponseEnvelopeMiddleware,
        time_provider=SystemTimeProvider(),
        api_version=DEFAULT_API_VERSION,
    )

    @app.get("/zwei-kekse")
    async def zwei_kekse() -> JSONResponse:
        antwort = JSONResponse(content={"ok": True})
        antwort.raw_headers.append((b"set-cookie", b"a=1; Path=/"))
        antwort.raw_headers.append((b"set-cookie", b"b=2; Path=/"))
        return antwort

    @app.get("/nichts")
    async def nichts() -> Response:
        return Response(status_code=204)

    return app


async def _get(pfad: str) -> HttpxResponse:
    transport = ASGITransport(app=_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(pfad)


async def test_mehrfach_gesetzte_kopfzeilen_ueberleben_das_einpacken() -> None:
    """Regression: gesetzt statt angehaengt loeschte das erste `Set-Cookie`."""
    antwort = await _get("/zwei-kekse")

    kekse = [wert for name, wert in antwort.headers.multi_items() if name == "set-cookie"]
    assert kekse == ["a=1; Path=/", "b=2; Path=/"]


async def test_der_content_type_beschreibt_den_neuen_koerper() -> None:
    """Genau einer, nicht zwei - der alte beschreibt einen Koerper, den es nicht mehr gibt."""
    antwort = await _get("/zwei-kekse")

    typen = [wert for name, wert in antwort.headers.multi_items() if name == "content-type"]
    assert typen == ["application/json"]


async def test_das_openapi_dokument_bekommt_keinen_umschlag() -> None:
    """Regression: eingepackt war es keine Beschreibung mehr, und `/docs` blieb leer.

    `/openapi.json` antwortet 200 in `application/json` und erfuellte damit beide
    Bedingungen des Umschlags. Swagger UI sucht `openapi` und `paths` an der
    Wurzel und fand `data` und `meta`.
    """
    antwort = await _get("/openapi.json")

    assert antwort.status_code == 200
    assert set(antwort.json()) >= {"openapi", "paths"}
    assert "data" not in antwort.json()


async def test_eine_antwort_ohne_koerper_bekommt_keinen_umschlag() -> None:
    """204 traegt nichts, was man einpacken koennte - die Kennung geht trotzdem mit."""
    antwort = await _get("/nichts")

    assert antwort.status_code == 204
    assert antwort.content == b""
    assert antwort.headers["X-Request-Id"]


@pytest.mark.parametrize("pfad", ["/zwei-kekse", "/nichts", "/openapi.json"])
async def test_jede_antwort_traegt_no_store(pfad: str) -> None:
    """Der Nachtrag an der Beschreibung sagt "immer `no-store`" - auch ohne Umschlag.

    Vorher setzte nur der eingepackte Zweig die Kopfzeile. Eine 204 und das
    Dokument selbst bekamen sie nie, obwohl `src/api/openapi.py` sie an jeder
    Antwort auswies.
    """
    antwort = await _get(pfad)

    assert antwort.headers["Cache-Control"] == "no-store"
