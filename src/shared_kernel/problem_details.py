"""RFC 7807 Problem Details model for structured error responses."""

from typing import Any, final

from pydantic import BaseModel, Field


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

    model_config = {"json_schema_extra": {"examples": [
        {
            "type": "https://api.example/errors/product-not-found",
            "title": "Produkt nicht gefunden",
            "status": 404,
            "detail": "Zu EAN 4008400401027 existiert kein Produkt.",
            "instance": "/api/v1/catalog/products/by-barcode/4008400401027",
            "errors": None,
        },
        {
            "type": "https://api.example/errors/validation-failed",
            "title": "Validierung fehlgeschlagen",
            "status": 400,
            "detail": "Die Eingabe erfüllt nicht die erforderlichen Bedingungen.",
            "instance": "/api/v1/identity/register",
            "errors": {
                "password": ["Mindestens 10 Zeichen erforderlich"],
                "email": ["Ungültiges E-Mail-Format"],
            },
        },
    ]}}
