"""RFC 7807 Problem Details model for structured error responses."""

from collections.abc import Mapping
from typing import final

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.i18n import language_of, resources_of, translate

__all__ = [
    "PROBLEM_JSON_MEDIA_TYPE",
    "PROBLEM_TYPE_PREFIX",
    "ProblemDetails",
    "ProblemResponse",
    "problem",
    "problem_type",
    "translated_problem",
]

PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"
"""Der Media-Type, unter dem eine Fehlerantwort dieser API ausgeliefert wird (RFC 7807).

An **einer** Stelle und nicht je Antwort: der Wert gehoert zur API als Ganzes,
und eine Stelle, die ihn selbst hinschreibt, kann ihn als einzige falsch
schreiben.
"""

PROBLEM_TYPE_PREFIX = "tag:nutritrack.app,2026:problems/"
"""Das Schema, unter dem jeder Fehlertyp dieser API benannt ist.

Ein `tag:`-URI nach RFC 4151 und keine `https:`-Adresse: der Typ ist ein
**Bezeichner**, nichts, was man abrufen koennte. Eine `https:`-Form verspricht
eine Seite, die es nicht gibt, und bindet die Bezeichner an einen Hostnamen, der
sich aendern kann.

Der Wert steht ohne Matcher im Vertrag des Frontends und ist damit bindend
(`contracts/pacts/identity/`, Ticket #95).
"""


def problem_type(slug: str) -> str:
    """Baue den Fehlertyp zu einem Fehlercode.

    An **einer** Stelle und nicht je Route: der Praefix gehoert zur API als
    Ganzes, und ein Endpunkt, der ihn selbst zusammensetzt, kann ihn als
    einziger falsch schreiben.
    """
    return f"{PROBLEM_TYPE_PREFIX}{slug}"


@final
class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details response model.

    Structured error format for REST APIs with support for domain-specific
    validation error details.
    """

    type: str = Field(description="URI identifying the error type")
    title: str = Field(description="Short, human-readable error title")
    status: int = Field(
        ge=400,
        le=599,
        description="HTTP status code (4xx or 5xx)",
    )
    detail: str = Field(description="Human-readable error detail")
    instance: str = Field(description="URI identifying the specific problem instance")
    errors: dict[str, list[str]] | None = Field(
        default=None,
        description="Field-level validation errors: fieldname -> [error messages]",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "tag:nutritrack.app,2026:problems/product-not-found",
                    "title": "Produkt nicht gefunden",
                    "status": 404,
                    "detail": "Zu EAN 4008400401027 existiert kein Produkt.",
                    "instance": "/api/v1/catalog/products/by-barcode/4008400401027",
                    "errors": None,
                },
                {
                    "type": "tag:nutritrack.app,2026:problems/validation-failed",
                    "title": "Validierung fehlgeschlagen",
                    "status": 422,
                    "detail": "Die Eingabe erfüllt nicht die erforderlichen Bedingungen.",
                    "instance": "/api/v1/identity/register",
                    "errors": {
                        "password": ["Mindestens 10 Zeichen erforderlich"],
                        "email": ["Ungültiges E-Mail-Format"],
                    },
                },
            ]
        }
    }


@final
class ProblemResponse(JSONResponse):
    """Die HTTP-Antwort, die einen `ProblemDetails`-Koerper traegt.

    Eine eigene Klasse und kein `JSONResponse` mit `media_type=`-Argument: der
    Media-Type gehoert zur Form und nicht zur Aufrufstelle. Damit steht in der
    Signatur eines Endpunkts, **welche** Antwort er im Fehlerfall liefert,
    statt nur "irgendein JSON".

    Warum ueberhaupt eine Response und nicht das nackte `ProblemDetails`-Modell:
    FastAPI nimmt den Media-Type aus der `response_class` der **Route** und
    nicht aus dem einzelnen Rueckgabewert (`fastapi/routing.py`, Zweig fuer
    Nicht-Response-Rueckgaben). Ein zurueckgegebenes Modell traege deshalb
    `application/json` - und damit nicht mehr, was RFC 7807 und der Vertrag des
    Frontends verlangen (`contracts/pacts/identity/`). Die `response_class` der
    Route umzustellen scheidet aus: sie gilt auch fuer die 201.
    """

    media_type = PROBLEM_JSON_MEDIA_TYPE


def problem(  # noqa: PLR0913, PLR0917 -- API response builder needs context, status, type, and text
    request: Request,
    http_status: int,
    error_type: str,
    title: str,
    detail: str,
    errors: dict[str, list[str]] | None = None,
    *,
    language_tag: str,
) -> ProblemResponse:
    """Baue eine RFC-7807-Antwort im Format des Shared Kernel.

    `language_tag` hat bewusst **keinen** Vorgabewert: `title` und `detail` sind
    beim Aufruf bereits uebersetzt, und ein Vorgabewert liesse sich vergessen,
    ohne dass etwas auffaellt - der Aufrufer bekaeme dann einen englischen Text
    mit `Content-Language: de-DE`. Wer die Antwort baut, hat die ausgehandelte
    Sprache ohnehin in der Hand.
    """
    details = ProblemDetails(
        type=problem_type(error_type),
        title=title,
        status=http_status,
        detail=detail,
        instance=str(request.url.path),
        errors=errors,
    )
    response = ProblemResponse(
        status_code=http_status,
        content=details.model_dump(exclude_none=True),
    )
    response.headers["Content-Language"] = language_tag
    # Die Umschlag-Middleware setzt denselben Header, aber nur auf 2xx -
    # Fehlerkoerper laufen an ihr bewusst vorbei. Hier ist die eine Stelle, an
    # der jede RFC-7807-Antwort dieses Repos entsteht; ein Endpunkt, der ihn
    # selbst setzte, koennte ihn als einziger vergessen. Doppelt gesetzt wird er
    # nie: keine Fehlerantwort traegt einen Umschlag.
    #
    # Bindend laut Vertrag des Frontends (`contracts/pacts/identity/`,
    # Ticket #95): diese API antwortet mit Kontodaten, und das gilt fuer
    # Fehlerkoerper genauso.
    response.headers["Cache-Control"] = "no-store"
    return response


def translated_problem(  # noqa: PLR0913 -- siehe Hinweis im Docstring
    request: Request,
    http_status: int,
    slug: str,
    *,
    resource_key: str | None = None,
    parameters: Mapping[str, object] | None = None,
    errors: dict[str, list[str]] | None = None,
) -> ProblemResponse:
    """Baue eine RFC-7807-Antwort samt ihren beiden Uebersetzungen.

    Die eine Stelle, an der eine Fehlerantwort dieser API **entsteht**: `title`
    steht unter `<resource_key>`, `detail` unter `<resource_key>-detail`.

    `resource_key` faellt auf `slug` zurueck, weil beide fast ueberall
    deckungsgleich sind. Der Rueckfall ist ein `or` und kein `is not None`: ein
    leerer Schluessel ist kein Schluessel, sondern derselbe Fall wie gar keiner -
    er wuerde sonst als `""` in die Ressourcen gehen und dort scheitern.

    Wo Slug und Schluessel auseinandergehen, wird der Schluessel genannt statt
    die Ressource umbenannt: der Slug steht im Fehlertyp und damit im Vertrag des
    Frontends (`contracts/pacts/identity/`), der Ressourcenschluessel nicht -
    eine Angleichung waere entweder ein Vertragsbruch oder eine Migration der
    Ressourcendateien. Einzige Abweichung im Repo: `request-in-progress` liest
    unter `idempotency-request-in-progress`.

    `parameters` fuellt die Platzhalter beider Vorlagen; ein Titel ohne
    Platzhalter ignoriert sie.

    Sprache und Ressourcen kommen aus der **Anfrage** und nicht als Argumente
    herein: beide folgen aus ihr (`language_of`, `resources_of` in
    `src/api/i18n.py`).

    Zum `noqa`: die Signatur zaehlt sechs Argumente, `PLR0913` erlaubt fuenf.
    Weniger sind es nicht - Anfrage, Status und Slug sind Pflicht, und
    `resource_key`, `parameters` und `errors` decken je eine Aufrufstelle ab,
    die es ohne sie nicht gibt. Nur `positional` ist es gedeckelt: nach dem
    dritten Argument ist Schluss, `PLR0917` greift nicht.
    """
    key = resource_key or slug
    language = language_of(request)
    resources = resources_of(request)
    return problem(
        request,
        http_status,
        slug,
        translate(resources, key, parameters, language),
        translate(resources, f"{key}-detail", parameters, language),
        errors,
        language_tag=language,
    )
