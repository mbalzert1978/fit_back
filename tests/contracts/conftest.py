"""What the contract tests find ready: finished Pacts and an app on the test database.

**Only here**, in this package, does a file get opened and `json` imported. A
test module receives the Pact as an object and the `Store` as a function; it
knows neither where the files live nor that they exist.
"""

import json
from collections.abc import Mapping
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.community.postgres import PostgresContainer

from tests.contracts.account import Account
from tests.contracts.idempotency_key import IdempotencyKey
from tests.contracts.provider_verification import Pact, Store

_PACTS = Path(__file__).parents[2] / "contracts/pacts"
"""The one place all pacts live (`docs/decisions/2026-08-21-1330-...`)."""

EMAIL = "a@b.de"
PASSWORD = "geheim123"
"""Data the identity pact's provider states name in plain text.

They live here because two things need them: the `account` fixture below and
the state names in the test module, which are composed from these.
"""

REUSED_KEY = "3f2a1b0c-4d5e-4f60-8a91-b2c3d4e5f607"
"""The key the reuse interaction sends - fixed in the pact, not generated.

A generated one couldn't be it: the value stands in the request the verifier
replays, so the state has to seed exactly this one.
"""


def _read(file: Path) -> Pact:
    return Pact.from_raw(json.loads(file.read_text(encoding="utf-8")))


@pytest.fixture
def identity_pact() -> Pact:
    """The frontend's pact against `nutritrack-identity` - the specification."""
    return _read(_PACTS / "identity/nutritrack-app-nutritrack-identity.json")


@pytest.fixture
def mechanik_pact() -> Pact:
    """The pact whose consumer is this repo itself - the proof.

    Origin and purpose of both files are in
    `contracts/pacts/identity/README.md`.
    """
    return _read(_PACTS / "identity/fit-back-mechanik-nutritrack-identity.json")


@pytest.fixture
def pact_store(tmp_path: Path) -> Store:
    """Where the pact to replay gets written, so the verifier can read it.

    In `tmp_path`, which pytest creates and tears down per test - the files
    under `contracts/pacts/` stay untouched.
    """

    def write(content: Mapping[str, object]) -> Path:
        file = tmp_path / "abzuspielen.json"
        file.write_text(json.dumps(content), encoding="utf-8")
        return file

    return write


@pytest_asyncio.fixture
async def account(postgres_engine: AsyncEngine) -> Account:
    """The one account the identity pact's register states revolve around.

    Both verification runs need the same account; their states differ only in
    which half maps to `create` and which to `remove`.
    """
    return Account(postgres_engine, email=EMAIL, password=PASSWORD)


@pytest_asyncio.fixture
async def idempotency_key(postgres_engine: AsyncEngine) -> IdempotencyKey:
    """The reserved key the register pact's reuse interaction runs into."""
    return IdempotencyKey(postgres_engine, key=REUSED_KEY)


@pytest_asyncio.fixture(autouse=True)
async def app_uses_test_database(
    postgres_service: PostgresContainer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Set the environment `validate_settings()` reads from at startup.

    Provider verification boots the real app, which builds its own engine from
    the environment. Without these values it aborts at startup - and a startup
    abort is a setup bug, not a contract violation.
    """
    monkeypatch.setenv("DB_HOST", postgres_service.get_container_host_ip())
    monkeypatch.setenv("DB_PORT", str(postgres_service.get_exposed_port(5432)))
    monkeypatch.setenv("DB_NAME", "test")
    monkeypatch.setenv("DB_USER", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")
    monkeypatch.setenv("JWT_SECRET", "test-geheimnis-mit-mindestens-32-zeichen")
