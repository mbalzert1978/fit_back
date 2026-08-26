"""Der Antwort-Umschlag: `{data, meta}` fuer jede erfolgreiche Antwort des Hosts.

Die `X-Request-Id` entsteht hier und wird nicht vom Aufrufer uebernommen - ein Wert aus
der Anfrage waere in Laenge und Zeichenvorrat fremdbestimmt.

Fehlerkoerper (`application/problem+json`) laufen an dieser Middleware vorbei; ihr
`Cache-Control: no-store` setzt `problem()` (`src/api/problem_details.py`) selbst.
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

__all__ = ["API_VERSION", "REQUEST_ID_HEADER", "ResponseEnvelopeMiddleware"]

API_VERSION: Final = "1"
"""Die Version, die `meta.apiVersion` nennt - dieselbe wie im Pfadpraefix `/api/v1`."""

REQUEST_ID_HEADER: Final = "X-Request-Id"

_JSON = "application/json"
_SUCCESS = range(200, 300)
_BODY_HEADERS = frozenset({b"content-length", b"content-type"})
"""Was den alten Koerper beschreibt und deshalb nicht mitwandert."""


@final
class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """Legt `{data, meta}` um jede erfolgreiche JSON-Antwort."""

    def __init__(self, app: ASGIApp, time_provider: TimeProvider) -> None:
        """Nimm die Zeitquelle entgegen - `meta.timestamp` kommt aus ihr, nicht aus `utcnow`."""
        super().__init__(app)
        self._clock = time_provider

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Lass die Anfrage laufen und packe ihr Ergebnis ein, wenn es eines ist."""
        request_id = str(uuid7())
        response = await call_next(request)
        if not _is_enveloped(response):
            response.headers[REQUEST_ID_HEADER] = request_id
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
            "apiVersion": API_VERSION,
            "requestId": request_id,
            # `Z` statt `+00:00`: die kurze Form ist die, die der Pact zeigt.
            "timestamp": self._clock.utc_now().isoformat().replace("+00:00", "Z"),
        }


def _is_enveloped(response: Response) -> bool:
    """Sage, ob diese Antwort einen Umschlag bekommt."""
    return response.status_code in _SUCCESS and response.headers.get("content-type", "").startswith(
        _JSON
    )
