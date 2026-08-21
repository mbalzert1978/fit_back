"""Gemeinsame Voraussetzung der Contract-Tests: die App zeigt auf die Testdatenbank."""

import pytest
import pytest_asyncio
from testcontainers.community.postgres import PostgresContainer


@pytest_asyncio.fixture(autouse=True)
async def app_zeigt_auf_die_testdatenbank(
    postgres_service: PostgresContainer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Setze die Umgebung, aus der `validate_settings()` beim Start liest.

    Die Provider-Verifikation faehrt die echte App hoch; die baut ihre Engine
    selbst aus der Umgebung. Ohne diese Werte bricht sie beim Start ab - und ein
    Abbruch beim Start ist ein Aufsetzfehler, kein Vertragsbruch.
    """
    monkeypatch.setenv("DB_HOST", postgres_service.get_container_host_ip())
    monkeypatch.setenv("DB_PORT", str(postgres_service.get_exposed_port(5432)))
    monkeypatch.setenv("DB_NAME", "test")
    monkeypatch.setenv("DB_USER", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")
