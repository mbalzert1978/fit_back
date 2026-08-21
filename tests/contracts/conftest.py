"""Was die Contract-Tests vorfinden: fertige Pacts und eine App auf der Testdatenbank.

**Hier und nur hier** wird in diesem Verzeichnis eine Datei angefasst und `json`
importiert. Ein Testmodul bekommt den Pact als Objekt gereicht und die `Ablage`
als Funktion; es weiss weder, wo die Dateien liegen, noch dass es welche gibt.
"""

import json
from collections.abc import Mapping
from pathlib import Path

import pytest
import pytest_asyncio
from testcontainers.community.postgres import PostgresContainer

from tests.contracts.provider_verification import Ablage, Pact

_PACTS = Path(__file__).parents[2] / "contracts/pacts"
"""Der eine Ablageort aller Pacts (`docs/decisions/2026-08-21-1330-...`)."""


def _gelesen(datei: Path) -> Pact:
    """Lies eine Pact-Datei und deute sie."""
    return Pact.von(json.loads(datei.read_text(encoding="utf-8")))


@pytest.fixture
def identity_pact() -> Pact:
    """Der Pact des Frontends gegen `nutritrack-identity` - die Vorgabe."""
    return _gelesen(_PACTS / "identity/nutritrack-app-nutritrack-identity.json")


@pytest.fixture
def mechanik_pact() -> Pact:
    """Der Pact, dessen Konsument dieses Repo selbst ist - der Nachweis.

    Herkunft und Zweck beider Dateien stehen in
    `contracts/pacts/identity/README.md`.
    """
    return _gelesen(_PACTS / "identity/fit-back-mechanik-nutritrack-identity.json")


@pytest.fixture
def pact_ablage(tmp_path: Path) -> Ablage:
    """Wohin der abzuspielende Pact geschrieben wird, damit der Verifier ihn liest.

    In `tmp_path`, das pytest je Test anlegt und wieder wegraeumt - die Dateien
    unter `contracts/pacts/` bleiben unberuehrt.
    """

    def ablegen(inhalt: Mapping[str, object]) -> Path:
        datei = tmp_path / "abzuspielen.json"
        datei.write_text(json.dumps(inhalt), encoding="utf-8")
        return datei

    return ablegen


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
