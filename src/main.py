"""Fit-back API entry point."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from src.api.composition import build_engine, build_event_registry, run_outbox_worker
from src.api.exception_handlers import register_exception_handlers
from src.api.identity import register_user_router
from src.shared_infrastructure.idempotency import IdempotencyKeyMiddleware
from src.shared_kernel.time_provider import SystemTimeProvider

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application settings with validation."""

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="fit_back")
    db_user: str = Field(default="fit_user")
    db_password: str = Field(...)  # Required, no default

    @property
    def database_url(self) -> str:
        """SQLAlchemy-URL fuer dieselbe Datenbank.

        Der asyncpg-Pool unten und diese Engine sprechen mit derselben Instanz,
        aber ueber zwei Wege: der Pool bedient Health-Check und
        Idempotency-Middleware (Tickets 0001/0006), die Engine die Slices. Ein
        Weg zu viel - beim naechsten Anfassen von 0006 zusammenfuehren.
        """
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


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
        logger.warning("Failed to initialize database pool")
        raise


async def close_db(pool: asyncpg.Pool | None) -> None:
    """Close database connection pool."""
    if pool:
        await pool.close()
        logger.info("Database pool closed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage app lifespan: startup and shutdown."""
    # Startup: validate settings and initialize database
    try:
        settings = validate_settings()
        app.state.settings = settings
        app.state.db_pool = await init_db(settings)
        # Set up idempotency middleware after db pool is ready
        setup_idempotency_middleware(app)
    except RuntimeError as e:
        logger.error("Application startup failed: %s", str(e))
        app.state.db_pool = None
        raise

    app.state.engine = build_engine(settings.database_url)
    app.state.event_registry = build_event_registry()
    async with run_outbox_worker(app.state.engine, app.state.event_registry):
        yield

    # Shutdown
    await app.state.engine.dispose()
    await close_db(app.state.db_pool)


app = FastAPI(title="Fit-back API", lifespan=lifespan)

# Register exception handlers for RFC 7807 ProblemDetails
register_exception_handlers(app)

# Rate-Limit- und CSRF-Middleware sind hier bewusst nicht verdrahtet: beide kamen
# aus 96b8f2c, wurden mit 4165fed zurueckgenommen (siehe
# docs/decisions/2026-08-05-0936-security-gate-triage-ticket-0001.md) und sind
# ueber den PR-Merge c30054d unbemerkt zurueckgekehrt - inklusive zweier Importe,
# die es nicht gibt (`fastapi.middleware.base`, `starlette.middleware.csrf`).
# Seither liess sich dieses Modul nicht mehr importieren, ohne dass es auffiel:
# nichts hat es je geladen. Der Smoke-Test in tests/api/test_app_startup.py
# schliesst diese Luecke.
app.include_router(register_user_router)


def setup_idempotency_middleware(app: FastAPI) -> None:
    """Set up idempotency middleware after database initialization.

    This is called in the lifespan startup after db_pool is initialized.
    """
    db_pool: asyncpg.Pool | None = getattr(app.state, "db_pool", None)
    if db_pool is None:
        logger.warning("Idempotency middleware skipped: database pool not initialized")
        return

    time_provider = SystemTimeProvider()
    app.add_middleware(
        IdempotencyKeyMiddleware,
        db_pool=db_pool,
        time_provider=time_provider,
    )


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
        logger.warning("Health check: database connection failed")
        return JSONResponse(
            {"status": "unhealthy"},
            status_code=503,
        )


def main() -> None:
    """Run the application."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
