"""RFC 7807 Problem Details model for structured error responses."""

from typing import final

from pydantic import BaseModel, Field

__all__ = ["PROBLEM_TYPE_PREFIX", "ProblemDetails", "problem_type"]

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
