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
    locale = getattr(request.state, "locale", "en-US")

    # Get resource provider from app state (required to be initialized by register_exception_handlers)
    resource_provider: ResourceProvider | None = getattr(
        request.app.state, "resource_provider", None
    )

    if not resource_provider:
        logger.error(
            "ResourceProvider not initialized in app state. "
            "Ensure register_exception_handlers() is called during app startup."
        )
        raise RuntimeError(
            "ResourceProvider not initialized. Call register_exception_handlers(app) during app startup."
        )

    # Extract error code from error_type (format: https://api.example/errors/error-code)
    # Validate format and convert from kebab-case to UPPERCASE_WITH_UNDERSCORES
    # Wrap validation in try-catch: exception handlers must be robust and never crash
    try:
        if not exc.error_type or "/" not in exc.error_type:
            raise ValueError(
                f"Invalid error_type format. Expected 'https://.../errors/<kebab-case>', "
                f"got: {exc.error_type!r}"
            )
        error_code_kebab = exc.error_type.split("/")[-1]
        if not error_code_kebab or not all(c.islower() or c == "-" for c in error_code_kebab):
            raise ValueError(
                f"error_type must end with kebab-case error code, "
                f"got: {error_code_kebab!r} from {exc.error_type!r}"
            )
        error_code = error_code_kebab.upper().replace("-", "_")
    except ValueError as e:
        # Handler validation failed: log and return RFC 7807 error response
        logger.error(
            "DomainException validation failed: %s. "
            "Falling back to generic error response.",
            str(e),
            extra={"error_type": exc.error_type},
        )
        problem = ProblemDetails(
            type="https://api.example/errors/internal-server-error",
            title="Internal Server Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request.",
            instance=str(request.url.path),
            errors=None,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=problem.model_dump(exclude_none=True),
            media_type="application/problem+json",
        )

    # Get localized title and detail; fall back to exception values if resource not found (locale-neutral)
    localized = resource_provider.get_message(error_code, locale)
    title = localized.get("title") or exc.title
    detail = localized.get("detail") or exc.detail

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
    locale = getattr(request.state, "locale", "en-US")

    # Get resource provider from app state (required to be initialized by register_exception_handlers)
    resource_provider: ResourceProvider | None = getattr(
        request.app.state, "resource_provider", None
    )

    if not resource_provider:
        logger.error(
            "ResourceProvider not initialized in app state. "
            "Ensure register_exception_handlers() is called during app startup."
        )
        raise RuntimeError(
            "ResourceProvider not initialized. Call register_exception_handlers(app) during app startup."
        )

    # Try to get localized title and detail for VALIDATION_FAILED
    # Fall back to English if resource not found (locale-neutral)
    localized = resource_provider.get_message("VALIDATION_FAILED", locale)
    title = localized.get("title") or "Validation failed"
    detail = localized.get("detail") or "Input does not meet the required conditions."

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

    Initializes ResourceProvider and stores it in app state for use in exception handlers.
    This function MUST be called during app startup before any requests are processed,
    as both domain_exception_handler and validation_exception_handler depend on
    ResourceProvider being available in app.state.resource_provider.

    Args:
        app: FastAPI application instance.

    Raises:
        RuntimeError: If resources directory cannot be initialized.
    """
    # Initialize ResourceProvider with default resources directory
    resources_dir = Path(__file__).parent / "resources"
    if not resources_dir.exists():
        raise RuntimeError(
            f"Resources directory not found: {resources_dir}. "
            "Exception handlers require resource files for localization."
        )

    resource_provider = ResourceProvider(resources_dir)
    app.state.resource_provider = resource_provider

    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
