import asyncio
import os
import subprocess
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.community.postgres import PostgresContainer


@pytest_asyncio.fixture(scope="session")
async def postgres_service() -> AsyncGenerator[PostgresContainer]:
    """Start and manage a Testcontainers PostgreSQL service."""
    container = PostgresContainer(
        image="postgres:17-alpine",
        username="test",
        password="test",
        dbname="test",
    )
    container.start()
    yield container
    container.stop()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def alembic_migrations(postgres_service: PostgresContainer) -> None:
    """Apply Alembic migrations to the test database."""
    # Extract connection parameters from container
    host = postgres_service.get_container_host_ip()
    port = postgres_service.get_exposed_port(5432)
    username = "test"
    password = "test"
    database = "test"

    # Build connection string for alembic
    db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"

    # Copy environment and set SQLALCHEMY_URL
    env = os.environ.copy()
    env["SQLALCHEMY_URL"] = db_url

    def _run_migrations() -> None:
        """Run alembic migrations in a blocking call."""
        try:
            subprocess.run(
                ["python", "-m", "alembic", "upgrade", "head"],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            msg = f"Alembic migration failed: {e.stderr}\n{e.stdout}"
            raise RuntimeError(msg) from e

    await asyncio.to_thread(_run_migrations)


@pytest_asyncio.fixture(scope="function")
async def postgres_engine(postgres_service: PostgresContainer) -> AsyncGenerator[AsyncEngine]:
    """Create a SQLAlchemy AsyncEngine connected to the test database."""
    # Extract connection parameters from container
    host = postgres_service.get_container_host_ip()
    port = postgres_service.get_exposed_port(5432)
    user = "test"
    password = "test"
    database = "test"

    # Create async engine URL
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def postgres_session(
    postgres_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    """Create a SQLAlchemy AsyncSession for testing."""
    async_session = sessionmaker(
        postgres_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
