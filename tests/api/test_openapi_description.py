"""Haelt die veroeffentlichte Beschreibung gegen das, was die Leitung wirklich tut.

FastAPI beschreibt den Rueckgabewert eines Endpunkts. Was der Aufrufer bekommt,
bauen danach noch zwei Middlewares um: `{data, meta}` legt sich um jede
erfolgreiche JSON-Antwort, und jeder Fehlerkoerper geht als
`application/problem+json` hinaus. Der Nachtrag dazu steht in
`src/api/openapi.py`; hier steht, dass er wirkt.

Was der Aufrufer wirklich empfaengt, pruefen
`tests/api/test_register_user_endpoint.py` und
`tests/middleware/test_response_envelope.py`. Dieser Test haelt nur beide
Seiten aneinander.
"""

from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.health_router import health_router
from src.api.identity import register_user_router
from src.api.openapi import ResponseMeta, document_middleware_effects
from src.api.problem_details import PROBLEM_JSON_MEDIA_TYPE
from src.contexts.shared_kernel.time_provider import SystemTimeProvider
from src.middleware.response_envelope import API_VERSION, ResponseEnvelopeMiddleware

_REGISTER = "/api/v1/identity/register"


def _document() -> dict[str, Any]:
    """Baue die Beschreibung aus denselben Routern wie `src/main.py`.

    Ohne Middleware und ohne Lifespan: das Dokument entsteht aus den Routen,
    nicht aus einem laufenden Host.
    """
    app = FastAPI(version=API_VERSION)
    app.include_router(health_router)
    app.include_router(register_user_router)
    document_middleware_effects(app)
    return app.openapi()


def _register_responses() -> dict[str, Any]:
    return _document()["paths"][_REGISTER]["post"]["responses"]


def test_die_erfolgsantwort_wird_als_umschlag_beschrieben() -> None:
    """Regression: das Dokument nannte `RegisterUserResponse` an der Wurzel.

    Ein daraus erzeugter Client haette `user` dort gesucht und `data` gefunden.
    """
    schema = _register_responses()["201"]["content"]["application/json"]["schema"]

    assert schema["required"] == ["data", "meta"]
    assert schema["properties"]["data"]["$ref"].endswith("/RegisterUserResponse")
    assert schema["properties"]["meta"]["$ref"].endswith("/ResponseMeta")


def test_fehlerkoerper_werden_als_problem_json_beschrieben() -> None:
    """Regression: `application/json` stand daneben.

    Das behauptete, der Aufrufer duerfe sich einen Media-Type aussuchen; diese
    API bietet nur den einen an.
    """
    for code in ("409", "422"):
        content = _register_responses()[code]["content"]
        assert set(content) == {PROBLEM_JSON_MEDIA_TYPE}
        assert content[PROBLEM_JSON_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetails")


def test_jede_antwort_nennt_die_kopfzeilen_des_hosts() -> None:
    """`X-Request-Id` und `Cache-Control` gelten fuer alles - also auch fuer alles im Dokument."""
    for path_item in _document()["paths"].values():
        for operation in path_item.values():
            for code, response in operation["responses"].items():
                assert "X-Request-Id" in response["headers"], f"{code} ohne X-Request-Id"
                assert "Cache-Control" in response["headers"], f"{code} ohne Cache-Control"


def test_die_201_nennt_ihre_eigenen_kopfzeilen() -> None:
    """`Location` und `Content-Language` gehoeren nur zu dieser einen Antwort."""
    headers = _register_responses()["201"]["headers"]

    assert set(headers) >= {"Location", "Content-Language"}


def test_die_dokumentversion_ist_die_version_dieser_api() -> None:
    """`info.version` nennt die API und nicht das Python-Paket.

    Es stand auf `0.1.0` - der Versionsnummer aus `pyproject.toml`. Der Pfad
    sagt `/api/v1`, `meta.apiVersion` sagt `1`; drei Angaben, von denen eine
    etwas anderes behauptete.

    Geprueft am echten `src/main.py`: dass der Nachtrag dort auch verdrahtet
    ist, steht sonst nirgends.
    """
    from src.main import app  # noqa: PLC0415 -- der Einstiegspunkt gehoert nicht in den Modulkopf

    assert app.openapi()["info"]["version"] == API_VERSION


@pytest.mark.asyncio
async def test_das_meta_modell_nennt_dieselben_felder_wie_die_middleware() -> None:
    """Drift-Pruefung: `ResponseMeta` wird nie gebaut, also merkt es sonst niemand.

    Das Modell beschreibt einen Block, den die Middleware selbst schreibt. Ohne
    diesen Test koennte es ein Feld nennen, das es nicht gibt - oder eines
    verschweigen.
    """
    app = FastAPI()
    app.add_middleware(ResponseEnvelopeMiddleware, time_provider=SystemTimeProvider())

    @app.get("/etwas")
    async def etwas() -> dict[str, bool]:
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        antwort = await client.get("/etwas")

    assert set(antwort.json()["meta"]) == set(
        ResponseMeta.model_json_schema(by_alias=True)["properties"]
    )
