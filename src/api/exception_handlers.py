"""Exception-Handler des HTTP-Randes.

Uebersetzt, was FastAPI selbst wirft, in das RFC-7807-Format. Fachliche
Fehlausgaenge laufen **nicht** hierueber: die tragen die Slices in ihrer
Response-Union, und der Router waehlt daraus Statuscode und Body. Ein
Exception-basierter zweiter Fehlerkanal daneben waere genau die Verzweigung,
die man beim Lesen nicht mehr sieht.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.problem_details import ProblemDetails

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors as RFC 7807 ProblemDetails.

    Returns 400 with field-level validation error details.
    """
    errors_dict: dict[str, list[str]] = {}
    for error in exc.errors():
        # Extract field name from location tuple, skipping "body"
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        message = error.get("msg", "Validation error")
        if field not in errors_dict:
            errors_dict[field] = []
        errors_dict[field].append(message)

    problem = ProblemDetails(
        type="https://api.example/errors/validation-failed",
        title="Validierung fehlgeschlagen",
        status=status.HTTP_400_BAD_REQUEST,
        detail="Die Eingabe erfüllt nicht die erforderlichen Bedingungen.",
        instance=str(request.url.path),
        errors=errors_dict if errors_dict else None,
    )
    logger.info(
        "Validation error at %s: %s fields",
        str(request.url.path),
        len(errors_dict),
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registriere die Exception-Handler an der App."""
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
