"""FastAPI exception handlers for domain errors and validation."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .exceptions import DomainException
from .problem_details import ProblemDetails

logger = logging.getLogger(__name__)


async def domain_exception_handler(
    request: Request,
    exc: DomainException,
) -> JSONResponse:
    """Handle domain exceptions and convert to RFC 7807 ProblemDetails.

    Returns 4xx/5xx status with structured error format.
    """
    instance = exc.instance or str(request.url.path)
    problem = ProblemDetails(
        type=exc.error_type,
        title=exc.title,
        status=exc.http_status,
        detail=exc.detail,
        instance=instance,
        errors=None,
    )
    logger.info(
        "Domain error: %s at %s",
        exc.error_type,
        instance,
        extra={"status": exc.http_status},
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


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
    """Register exception handlers in FastAPI app.

    Args:
        app: FastAPI application instance.
    """
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
