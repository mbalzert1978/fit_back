"""FastAPI exception handlers for domain errors and validation."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .exceptions import DomainException
from .problem_details import ProblemDetails
from .resources import ResourceProvider

logger = logging.getLogger(__name__)


async def domain_exception_handler(
    request: Request,
    exc: DomainException,
) -> JSONResponse:
    """Handle domain exceptions and convert to RFC 7807 ProblemDetails.

    Returns 4xx/5xx status with structured error format.
    Localizes title and detail from resource files based on Accept-Language header.
    """
    instance = exc.instance or str(request.url.path)

    # Extract locale from request state (set by AcceptLanguageMiddleware)
    locale = getattr(request.state, "locale", "de-DE")

    # Get resource provider from app state or create a new one
    resource_provider: ResourceProvider | None = getattr(
        request.app.state, "resource_provider", None
    )

    # Extract error code from error_type (format: https://api.example/errors/error-code)
    # Convert from kebab-case to UPPERCASE_WITH_UNDERSCORES for resource lookup
    error_code_kebab = exc.error_type.split("/")[-1]
    error_code = error_code_kebab.upper().replace("-", "_")

    # Get localized title and detail, or use exception values as fallback
    title = exc.title
    detail = exc.detail

    if resource_provider:
        localized = resource_provider.get_message(error_code, locale)
        if localized.get("title"):
            title = localized["title"]
        if localized.get("detail"):
            detail = localized["detail"]

    problem = ProblemDetails(
        type=exc.error_type,
        title=title,
        status=exc.http_status,
        detail=detail,
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
    Localizes title and detail based on Accept-Language header.
    """
    errors_dict: dict[str, list[str]] = {}
    for error in exc.errors():
        # Extract field name from location tuple, skipping "body"
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        message = error.get("msg", "Validation error")
        if field not in errors_dict:
            errors_dict[field] = []
        errors_dict[field].append(message)

    # Extract locale from request state (set by AcceptLanguageMiddleware)
    locale = getattr(request.state, "locale", "de-DE")

    # Get resource provider from app state or use defaults
    resource_provider: ResourceProvider | None = getattr(
        request.app.state, "resource_provider", None
    )

    # Try to get localized title and detail for VALIDATION_FAILED
    title = "Validierung fehlgeschlagen"
    detail = "Die Eingabe erfüllt nicht die erforderlichen Bedingungen."

    if resource_provider:
        localized = resource_provider.get_message("VALIDATION_FAILED", locale)
        if localized.get("title"):
            title = localized["title"]
        if localized.get("detail"):
            detail = localized["detail"]

    problem = ProblemDetails(
        type="https://api.example/errors/validation-failed",
        title=title,
        status=status.HTTP_400_BAD_REQUEST,
        detail=detail,
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

    Also initializes ResourceProvider and stores it in app state
    for use in exception handlers.

    Args:
        app: FastAPI application instance.
    """
    # Initialize ResourceProvider with default resources directory
    resources_dir = Path(__file__).parent / "resources"
    resource_provider = ResourceProvider(resources_dir)
    app.state.resource_provider = resource_provider

    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
