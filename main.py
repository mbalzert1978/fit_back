"""Fit-back API entry point."""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Callable, final

import asyncpg
from fastapi import FastAPI, Request
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.csrf import CSRFMiddleware

from src.shared_kernel.exception_handlers import register_exception_handlers

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application settings with validation."""

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="fit_back")
    db_user: str = Field(default="fit_user")
    db_password: str = Field(...)  # Required, no default


def validate_settings() -> Settings:
    """Validate and load settings from environment variables."""
    try:
        return Settings(
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "fit_back"),
            db_user=os.getenv("DB_USER", "fit_user"),
            db_password=os.getenv("DB_PASSWORD"),
        )
    except (ValidationError, ValueError) as e:
        raise RuntimeError("Configuration validation failed: invalid environment variables") from e


async def init_db(settings: Settings) -> asyncpg.Pool:
    """Initialize database connection pool."""
    try:
        pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            min_size=1,
            max_size=10,
        )
        logger.info("Database pool initialized successfully")
        return pool
    except asyncpg.Error:
        logger.error("Failed to initialize database pool")
        raise


async def close_db(pool: asyncpg.Pool | None) -> None:
    """Close database connection pool."""
    if pool:
        await pool.close()
        logger.info("Database pool closed")


@final
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times: dict[str, list[float]] = {}

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> JSONResponse:
        """Rate limit requests based on client IP."""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        window_start = current_time - 60

        if client_ip not in self.request_times:
            self.request_times[client_ip] = []

        self.request_times[client_ip] = [
            t for t in self.request_times[client_ip] if t > window_start
        ]

        if len(self.request_times[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client: {client_ip}")
            return JSONResponse(
                {"status": "error", "detail": "Too many requests"},
                status_code=429,
            )

        self.request_times[client_ip].append(current_time)
        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan: startup and shutdown."""
    # Startup: validate settings and initialize database
    try:
        settings = validate_settings()
        app.state.settings = settings
        app.state.db_pool = await init_db(settings)
    except RuntimeError as e:
        logger.error(f"Application startup failed: {str(e)}")
        app.state.db_pool = None
        raise
    yield
    # Shutdown
    await close_db(app.state.db_pool)


app = FastAPI(title="Fit-back API", lifespan=lifespan)

# Register exception handlers for RFC 7807 ProblemDetails
register_exception_handlers(app)

# Validate CSRF secret key (mandatory, no default)
_csrf_secret_key = os.getenv("SECRET_KEY")
if not _csrf_secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required and has no default")

# Add security middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(CSRFMiddleware, secret_key=_csrf_secret_key)


@app.get("/api/v1/health")
async def health_check(request: Request) -> JSONResponse:
    """
    Health check endpoint.

    Returns 200 if the database is connected, 503 otherwise.
    """
    db_pool: asyncpg.Pool | None = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        logger.warning("Health check: database not available")
        return JSONResponse(
            {"status": "unhealthy"},
            status_code=503,
        )

    try:
        # Verify connection by running a simple query
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return JSONResponse({"status": "healthy"})
    except asyncpg.Error:
        logger.error("Health check: database connection failed")
        return JSONResponse(
            {"status": "unhealthy"},
            status_code=503,
        )


def main() -> None:
    """Run the application."""
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
