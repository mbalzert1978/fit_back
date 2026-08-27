"""Der Antwort-Umschlag: `{data, meta}` fuer jede erfolgreiche Antwort des Hosts.

Die `X-Request-Id` entsteht hier und wird nicht vom Aufrufer uebernommen - ein Wert aus
der Anfrage waere in Laenge und Zeichenvorrat fremdbestimmt.

`X-Request-Id` und `Cache-Control: no-store` bekommt **jede** Antwort, eingepackt
oder nicht - sonst verspraeche der Nachtrag an der Beschreibung
(`src/api/openapi.py`) mehr, als die Leitung liefert.

Ohne Umschlag bleiben Fehlerkoerper (`application/problem+json`), Antworten ohne
JSON-Koerper und das OpenAPI-Dokument selbst - siehe `_is_the_api_description`.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Final, final
from uuid import uuid7

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from src.contexts.shared_kernel.time_provider import TimeProvider
from src.middleware.streamed_body import read_streamed_body

__all__ = ["REQUEST_ID_HEADER", "ResponseEnvelopeMiddleware"]

REQUEST_ID_HEADER: Final = "X-Request-Id"

_JSON = "application/json"
_SUCCESS = range(200, 300)
_BODY_HEADERS = frozenset({b"content-length", b"content-type"})
"""Was den alten Koerper beschreibt und deshalb nicht mitwandert."""


@final
class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """Legt `{data, meta}` um jede erfolgreiche JSON-Antwort."""

    def __init__(self, app: ASGIApp, time_provider: TimeProvider, api_version: str) -> None:
        """Nimm Zeitquelle und API-Version entgegen - beide gehoeren in `meta`, nicht ins Modul."""
        super().__init__(app)
        self._clock = time_provider
        self._api_version = api_version

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Lass die Anfrage laufen und packe ihr Ergebnis ein, wenn es eines ist."""
        request_id = str(uuid7())
        response = await call_next(request)
        if not _is_enveloped(request, response):
            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers["Cache-Control"] = "no-store"
            return response

        body = json.loads(await read_streamed_body(response))
        wrapped = JSONResponse(
            status_code=response.status_code,
            content={"data": body, "meta": self._meta(request_id)},
        )
        # Angehaengt und nicht gesetzt: `headers[name] = value` loescht vorhandene
        # Vorkommen desselben Namens - ein Endpunkt mit zwei `Set-Cookie` verloere das
        # erste, still.
        for name, value in response.raw_headers:
            if name.lower() not in _BODY_HEADERS:
                wrapped.raw_headers.append((name, value))
        wrapped.headers[REQUEST_ID_HEADER] = request_id
        wrapped.headers["Cache-Control"] = "no-store"
        return wrapped

    def _meta(self, request_id: str) -> dict[str, str]:
        """Baue den `meta`-Block der Antwort."""
        return {
            "apiVersion": self._api_version,
            "requestId": request_id,
            # `Z` statt `+00:00`: die kurze Form ist die, die der Pact zeigt.
            "timestamp": self._clock.utc_now().isoformat().replace("+00:00", "Z"),
        }


def _is_enveloped(request: Request, response: Response) -> bool:
    """Sage, ob diese Antwort einen Umschlag bekommt."""
    return (
        response.status_code in _SUCCESS
        and response.headers.get("content-type", "").startswith(_JSON)
        and not _is_the_api_description(request)
    )


def _is_the_api_description(request: Request) -> bool:
    """Sage, ob dieser Pfad das OpenAPI-Dokument der App selbst ist.

    Der Umschlag gilt fuer die Antworten **dieser** API, nicht fuer die
    Beschreibung, in der FastAPI sie ausliefert. Eingepackt waere sie keine
    Beschreibung mehr: `/docs` sucht `openapi` und `paths` an der Wurzel und
    faende `data` und `meta`.

    `/docs` und `/redoc` brauchen keinen eigenen Zweig - sie antworten in HTML
    und scheitern schon an der Pruefung des Content-Type.

    Gelesen wird die Adresse **an der App** und nicht als Literal: wer sie ueber
    `FastAPI(openapi_url=...)` verschiebt oder mit `None` abschaltet, verschiebt
    sie damit auch hier. Ein Literal koennte gegen sie driften.
    """
    return request.url.path == getattr(request.app, "openapi_url", None)
