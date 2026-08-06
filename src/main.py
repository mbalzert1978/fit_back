"""Fit-back API entry point."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

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
        """Die eine Datenbank-URL des Prozesses.

        Der Treiber ist asyncpg, gefahren wird er ueber SQLAlchemy - ein Weg,
        den sich Health-Check, Idempotency-Middleware und die Slices teilen.
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage app lifespan: startup and shutdown.

    Hier wird **nichts** mehr an die App gehaengt, was zu ihrer Gestalt gehoert:
    Router, Exception-Handler und Middleware stehen auf Modulebene fest. Der
    Lifespan legt ausschliesslich Laufzeit-Ressourcen an und raeumt sie weg.
    """
    settings = validate_settings()
    app.state.settings = settings
    app.state.engine = build_engine(settings.database_url)
    app.state.event_registry = build_event_registry()
    logger.info("Datenbank-Engine erstellt")

    try:
        async with run_outbox_worker(app.state.engine, app.state.event_registry):
            yield
    finally:
        await app.state.engine.dispose()
        logger.info("Datenbank-Engine geschlossen")


app = FastAPI(title="Fit-back API", lifespan=lifespan)

# Register exception handlers for RFC 7807 ProblemDetails
register_exception_handlers(app)

# Middleware gehoert auf Modulebene: Starlette baut die Kette beim ersten
# ASGI-Aufruf zusammen - und das ist der Lifespan-Aufruf selbst. Ein
# `add_middleware` waehrend des Startups kommt also immer zu spaet und wirft
# "Cannot add middleware after an application has started"; siehe
# docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md.
# Die Engine kann die Middleware deshalb nicht im Konstruktor bekommen - sie
# liest sie je Anfrage aus `app.state`.
app.add_middleware(IdempotencyKeyMiddleware, time_provider=SystemTimeProvider())

# Rate-Limit- und CSRF-Middleware sind hier bewusst nicht verdrahtet: beide kamen
# aus 96b8f2c, wurden mit 4165fed zurueckgenommen (siehe
# docs/decisions/2026-08-05-0936-security-gate-triage-ticket-0001.md) und sind
# ueber den PR-Merge c30054d unbemerkt zurueckgekehrt - inklusive zweier Importe,
# die es nicht gibt (`fastapi.middleware.base`, `starlette.middleware.csrf`).
# Seither liess sich dieses Modul nicht mehr importieren, ohne dass es auffiel:
# nichts hat es je geladen. Der Smoke-Test in tests/api/test_app_startup.py
# schliesst diese Luecke.
app.include_router(register_user_router)


@app.get("/api/v1/health")
async def health_check(request: Request) -> JSONResponse:
    """
    Health check endpoint.

    Returns 200 if the database is connected, 503 otherwise.
    """
    engine: AsyncEngine | None = getattr(request.app.state, "engine", None)
    if engine is None:
        logger.warning("Health check: database not available")
        return JSONResponse(
            {"status": "unhealthy"},
            status_code=503,
        )

    try:
        # Verify connection by running a simple query
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return JSONResponse({"status": "healthy"})
    except SQLAlchemyError:
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
