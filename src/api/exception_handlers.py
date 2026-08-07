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

from src.api.i18n import get_language_from_header, translate
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

    language = get_language_from_header(request.headers.get("accept-language"))
    title = translate("validation-failed", {}, language)
    detail = translate("validation-failed-detail", {}, language)

    problem = ProblemDetails(
        type="https://api.example/errors/validation-failed",
        title=title,
        status=status.HTTP_400_BAD_REQUEST,
        detail=detail,
        instance=str(request.url.path),
        errors=errors_dict or None,
    )
    logger.info(
        "Validation error at %s: %s fields",
        str(request.url.path),
        len(errors_dict),
    )
    response = JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
    response.headers["Content-Language"] = language
    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Registriere die Exception-Handler an der App."""
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
