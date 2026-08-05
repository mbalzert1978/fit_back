"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def db_pool() -> None:
    """Mock database pool fixture.

    In production, this would be a real asyncpg.Pool.
    For unit tests that don't need DB access, return None.
    Integration tests can override this fixture.
    """
    return
