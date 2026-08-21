"""Der Antwort-Umschlag: `{data, meta}` fuer jede erfolgreiche Antwort des Hosts.

Eine Middleware und kein Router-Baustein. Der Umschlag ist eine Zusage der API
als Ganzes, nicht die eines Endpunkts: der naechste Endpunkt bekommt ihn ohne
eigene Zeile, und keiner kann ihn vergessen oder anders bauen (Ticket #95).

Drei Dinge tut sie, und nur diese drei:

1. **Die Anfrage-Kennung.** `X-Request-Id` geht an *jede* Antwort - auch an die
   fehlerhafte, denn genau die will man spaeter im Log wiederfinden. Sie entsteht
   **hier** und wird nicht vom Aufrufer uebernommen: ein Wert aus der Anfrage
   waere in Laenge und Zeichenvorrat fremdbestimmt und landete ungeprueft im Log
   und im Antwortkoerper.
2. **Der Umschlag, nur um 2xx.** Fehlerkoerper sind `application/problem+json`
   nach RFC 7807 und im Vertrag **nicht** eingepackt - ein Umschlag darum waere
   ein zweites Format fuer dieselbe Sache.
3. **`Cache-Control: no-store` auf 2xx.** Diese API antwortet mit Kontodaten und
   Token; ein Zwischenspeicher hat davon nichts zu behalten.

Was sie nicht anfasst: Antworten ohne Koerper (204, 304), Weiterleitungen und
alles, was nicht `application/json` ist. Ein Umschlag um einen Datei-Download
waere kaputt, nicht einheitlich.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Final, final
from uuid import uuid7

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.contexts.shared_kernel.time_provider import TimeProvider

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

    def __init__(self, app: Callable[..., object], time_provider: TimeProvider) -> None:
        """Nimm die Zeitquelle entgegen - `meta.timestamp` kommt aus ihr, nicht aus `utcnow`."""
        super().__init__(app)  # type: ignore[arg-type]
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

        body = json.loads(await _body_of(response))
        wrapped = JSONResponse(
            status_code=response.status_code,
            content={"data": body, "meta": self._meta(request_id)},
        )
        # Die Kopfzeilen der urspruenglichen Antwort bleiben, bis auf die, die
        # den alten Koerper beschreiben: Laenge und Typ gelten nach dem
        # Einpacken nicht mehr, und `JSONResponse` hat beide fuer den neuen
        # bereits gesetzt.
        #
        # Angehaengt und nicht gesetzt: `headers[name] = value` loescht
        # vorhandene Vorkommen desselben Namens. Ein Endpunkt mit zwei
        # `Set-Cookie` verloere so das erste, still.
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
            # `Z` statt `+00:00`: beides ist ISO 8601, aber die kurze Form ist
            # die, die der Vertrag zeigt.
            "timestamp": self._clock.utc_now().isoformat().replace("+00:00", "Z"),
        }


def _is_enveloped(response: Response) -> bool:
    """Sage, ob diese Antwort einen Umschlag bekommt."""
    # Eine Antwort ohne Koerper (204) traegt auch keinen `Content-Type` und
    # faellt damit schon ueber die zweite Bedingung heraus.
    return response.status_code in _SUCCESS and response.headers.get("content-type", "").startswith(
        _JSON
    )


async def _body_of(response: Response) -> bytes:
    """Lies den Koerper der Antwort einmal vollstaendig ein.

    `BaseHTTPMiddleware` reicht jede nachgelagerte Antwort als
    `_StreamingResponse` weiter - auch die, die weiter innen ein `JSONResponse`
    war. Ihr Koerper steht nur ueber `body_iterator` zur Verfuegung, und nur
    genau einmal; deshalb wird er hier eingesammelt und danach neu aufgebaut.
    """
    return b"".join([chunk async for chunk in response.body_iterator])  # type: ignore[attr-defined]
