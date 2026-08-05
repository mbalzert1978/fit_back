import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_postgres_connection(postgres_session: AsyncSession) -> None:
    """Test that the PostgreSQL connection is working."""
    result = await postgres_session.execute(text("SELECT 1"))
    value = result.scalar()
    assert value == 1


@pytest.mark.asyncio
async def test_alembic_migration_applied(postgres_session: AsyncSession) -> None:
    """Test that all required schemas exist after Alembic migration."""
    required_schemas = {
        "identity",
        "catalog",
        "diary",
        "recipes",
        "goals",
        "health_sync",
        "shared_kernel",
    }

    query = text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = ANY(:schemas)"
    )
    result = await postgres_session.execute(
        query,
        {"schemas": list(required_schemas)},
    )
    existing_schemas = {row[0] for row in result.fetchall()}

    assert existing_schemas == required_schemas, (
        f"Missing schemas: {required_schemas - existing_schemas}"
    )
