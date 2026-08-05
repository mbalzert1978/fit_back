"""Fit-back API entry point."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def init_db() -> asyncpg.Pool:
    """Initialize database connection pool."""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "fit_back")
    db_user = os.getenv("DB_USER", "fit_user")
    db_password = os.getenv("DB_PASSWORD", "fit_password")

    pool = await asyncpg.create_pool(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=10,
    )
    logger.info("Database pool initialized successfully")
    return pool


async def close_db(pool: asyncpg.Pool) -> None:
    """Close database connection pool."""
    if pool:
        await pool.close()
        logger.info("Database pool closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan: startup and shutdown."""
    # Startup
    try:
        app.state.db_pool = await init_db()
    except asyncpg.Error as e:
        logger.warning(f"Failed to initialize database pool: {e}")
        app.state.db_pool = None
    yield
    # Shutdown
    await close_db(app.state.db_pool)


app = FastAPI(title="Fit-back API", lifespan=lifespan)


@app.get("/api/v1/health")
async def health_check(request: Request) -> JSONResponse:
    """
    Health check endpoint.

    Returns 200 if the database is connected, 503 otherwise.
    """
    db_pool: asyncpg.Pool | None = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        logger.warning("Health check: database pool not initialized")
        return JSONResponse(
            {"status": "unhealthy", "detail": "database pool not initialized"},
            status_code=503,
        )

    try:
        # Verify connection by running a simple query
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return JSONResponse({"status": "healthy"})
    except asyncpg.Error as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            {"status": "unhealthy", "detail": str(e)},
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
