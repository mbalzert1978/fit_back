"""Outbox relay worker entry point for Docker/background process.

This module is the __main__ entry point for the relay worker when running
in a separate container or process (e.g., via `docker compose up`).

Usage:
    python -m src.shared_kernel.outbox.worker
"""

import asyncio
import logging
import os
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.shared_kernel.outbox import relay_outbox_events
from src.shared_kernel.outbox.relay import RelayConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the outbox relay worker."""
    # Read configuration from environment
    db_url = os.environ.get("SQLALCHEMY_DATABASE_URL")
    if not db_url:
        raise ValueError("SQLALCHEMY_DATABASE_URL environment variable is required")

    worker_id_str = os.environ.get("WORKER_ID")
    if worker_id_str:
        try:
            worker_id = UUID(worker_id_str)
        except ValueError as e:
            raise ValueError(f"Invalid WORKER_ID format: {e}") from e
    else:
        worker_id = uuid4()

    logger.info(f"Starting outbox relay worker {worker_id}")
    logger.info(f"Database URL: {db_url.split('@')[0] if '@' in db_url else '***'}")

    # Create async engine
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Create sessionmaker
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        # Run relay worker
        async with async_session() as session:
            config = RelayConfig(
                batch_size=10,
                max_retries=3,
                backoff_base_ms=100.0,
                poll_interval_ms=1000.0,
            )
            await relay_outbox_events(session, worker_id=worker_id, config=config)
    except asyncio.CancelledError:
        logger.info(f"Worker {worker_id} cancelled")
    except Exception:
        logger.exception(f"Worker {worker_id} encountered an error")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
