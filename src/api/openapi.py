"""Der Nachtrag an der veroeffentlichten Beschreibung: was die Middleware noch anlegt.

FastAPI beschreibt, was ein Endpunkt **zurueckgibt**. Was der Aufrufer wirklich
empfaengt, entsteht erst danach:

- `ResponseEnvelopeMiddleware` legt `{data, meta}` um jede erfolgreiche
  JSON-Antwort und setzt `X-Request-Id` und `Cache-Control`.
- Jeder Fehlerkoerper dieser API verlaesst sie als `application/problem+json`
  und nicht als `application/json` (`src/api/problem_details.py`).

Nichts davon sieht FastAPI, also stand nichts davon im erzeugten Dokument - und
eine Beschreibung, die etwas anderes verspricht als die Leitung liefert, ist
schaedlicher als gar keine. Ein Client, der aus ihr erzeugt wird, sucht `user`
an der Wurzel und findet `data`.

Der Nachtrag greift am **ganzen** Dokument und nicht je Route, weil auch die
Middleware am ganzen Host greift: eine neue Route ist damit von selbst richtig
beschrieben, und niemand kann den Nachtrag an einer Stelle vergessen.

Was nur zu **einer** Route gehoert, steht nicht hier, sondern in deren
`responses` - etwa `Location` und `Content-Language` der 201 von
`POST /api/v1/identity/register`.
"""

from typing import Any, Final, final

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.api.problem_details import PROBLEM_JSON_MEDIA_TYPE
from src.middleware.response_envelope import REQUEST_ID_HEADER
from src.settings import DEFAULT_API_VERSION

__all__ = ["ResponseMeta", "document_middleware_effects"]

_JSON: Final = "application/json"
_SUCCESS: Final = range(200, 300)
_META_REF: Final = "#/components/schemas/ResponseMeta"

_METHODS: Final = frozenset({"get", "put", "post", "delete", "options", "head", "patch", "trace"})
"""Was in einem Pfad-Eintrag eine Operation ist.

Daneben stehen dort auch `summary`, `description` und `parameters` - Eintraege
ohne `responses`, die dieser Nachtrag nicht anfassen darf.
"""


@final
class ResponseMeta(BaseModel):
    """Der `meta`-Block, den `ResponseEnvelopeMiddleware` an jede erfolgreiche Antwort haengt.

    Das Modell wird nie gebaut: den Block schreibt die Middleware selbst. Es
    steht hier, damit die Beschreibung seine drei Felder **nennt**, statt ein
    formloses Objekt zu zeigen.

    Dass beide Seiten zusammenbleiben, haelt ein Test fest - sonst koennte das
    Modell hier von dem abweichen, was die Middleware wirklich schreibt.
    """

    api_version: str = Field(
        alias="apiVersion",
        description="Die Version dieser API - dieselbe wie im Pfadpraefix.",
        examples=[DEFAULT_API_VERSION],
    )
    request_id: str = Field(
        alias="requestId",
        description="Die Kennung dieses Aufrufs, auch als Kopfzeile X-Request-Id.",
    )
    timestamp: str = Field(
        description="Der Zeitpunkt der Antwort, UTC in ISO 8601 mit `Z`.",
        examples=["2026-08-26T10:15:30.123456Z"],
    )


def document_middleware_effects(app: FastAPI, api_version: str) -> None:
    """Haenge den Nachtrag an die Beschreibung dieser App.

    Aufzurufen, **nachdem** alle Router eingehaengt sind: der Nachtrag laeuft
    ueber die Pfade des fertigen Dokuments.

    `api_version` steht hier und nicht nur an `FastAPI(version=...)`: sonst
    traegt der Nachtrag drei der vier Angaben, und die vierte haengt daran, dass
    der Aufrufer sie selbst gesetzt hat.

    `app.openapi()` erzeugt das Dokument und legt es in `app.openapi_schema` ab;
    dort wird es hier ergaenzt. Jeder spaetere Aufruf - auch der von
    `/openapi.json` - findet den Zwischenspeicher gefuellt und liefert die
    ergaenzte Fassung.

    Kein Nachbau von `get_openapi(...)`: der muesste jedes Feld der App von Hand
    weiterreichen und ginge still schief, sobald eines dazukommt. Und kein
    Ersetzen von `app.openapi` - eine gewoehnliche Funktion ist an dieser Stelle
    keine Methode, und das Repo laesst dafuer kein `type: ignore` zu.
    """
    app.openapi_schema = _amended(app.openapi(), api_version)


def _amended(document: dict[str, Any], api_version: str) -> dict[str, Any]:
    """Trage in jede Antwort des Dokuments ein, was die Middleware an ihr aendert."""
    document.setdefault("info", {})["version"] = api_version

    schemas = document.setdefault("components", {}).setdefault("schemas", {})
    schemas["ResponseMeta"] = ResponseMeta.model_json_schema(by_alias=True)

    for path_item in document.get("paths", {}).values():
        for method, operation in path_item.items():
            if method not in _METHODS:
                continue
            for code, response in operation.get("responses", {}).items():
                _amend_response(code, response)
    return document


def _amend_response(code: str, response: dict[str, Any]) -> None:
    """Trage Kopfzeilen, Umschlag und Media-Type in eine einzelne Antwort ein.

    Die beiden Kopfzeilen gelten fuer **jede** Antwort: die Umschlag-Middleware
    setzt sie auf beiden Wegen, eingepackt wie nicht eingepackt.

    `setdefault` und nicht `=`: was eine Route selbst ueber eine Kopfzeile sagt,
    weiss mehr als dieser Nachtrag und bleibt stehen.
    """
    headers = response.setdefault("headers", {})
    headers.setdefault(
        REQUEST_ID_HEADER,
        {
            "description": "Die Kennung dieses Aufrufs; sie steht auch in `meta.requestId`.",
            "schema": {"type": "string", "format": "uuid"},
        },
    )
    headers.setdefault(
        "Cache-Control",
        {
            "description": "Immer `no-store` - keine Antwort dieser API wird zwischengespeichert.",
            "schema": {"type": "string"},
        },
    )

    content = response.get("content")
    if not code.isdigit() or content is None or _JSON not in content:
        return

    if int(code) in _SUCCESS:
        content[_JSON]["schema"] = _envelope(content[_JSON]["schema"])
        return

    # Umgehaengt statt ergaenzt: unter `application/json` liefert diese API
    # keinen Fehlerkoerper aus, und beide Eintraege nebeneinander behaupteten,
    # der Aufrufer duerfe sich einen aussuchen.
    content[PROBLEM_JSON_MEDIA_TYPE] = content.pop(_JSON)


def _envelope(schema: dict[str, Any]) -> dict[str, Any]:
    """Lege die Form `{data, meta}` um ein Schema."""
    return {
        "type": "object",
        "required": ["data", "meta"],
        "properties": {"data": schema, "meta": {"$ref": _META_REF}},
    }
