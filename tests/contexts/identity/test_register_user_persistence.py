"""Integrationstests des Use Case RegisterUser gegen echte Infrastruktur.

Eine andere Ebene als die Specs unter `src/contexts/identity/specs/`
(docs/milestones/02-test-pyramide.md). Dort steckt hinter der Naht ein Fake und
geprueft wird das Verhalten des Use Case; hier steckt dahinter Postgres, Argon2id
und die Outbox, und geprueft wird ausschliesslich, was ein Fake **nicht** zeigen
kann:

- dass Nutzer-Zeile und Outbox-Zeile an derselben Transaktion haengen,
- dass der Unique-Constraint die Eindeutigkeit tatsaechlich entscheidet,
- dass im Feld ein echter Argon2id-Hash landet und kein Klartext,
- dass das gemeldete Ereignis den Weg bis zu einem registrierten Handler findet.

Verhaltensfragen des Use Case gehoeren nicht hierher - sie sind ueber die
Test-API billiger und schaerfer zu stellen.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from argon2 import PasswordHasher as Argon2
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegisterUserRequest,
    RegistrationAccepted,
)
from src.contexts.identity.application.register_user.adapters.test_api.fakes import (
    FixedTokenOptions,
)
from src.contexts.identity.application.register_user.pipeline import build_register_user_pipeline
from src.contexts.identity.contracts import UserRegistered
from src.contexts.identity.infrastructure.hashing import Argon2PasswordHasher
from src.contexts.identity.infrastructure.idn import IdnaLabels
from src.contexts.identity.infrastructure.persistence import PostgresUserStore
from src.contexts.identity.infrastructure.tokens import JwtAccessTokens, PostgresSessionTokens
from src.contexts.shared_kernel.events import DeliveredEvent, EventRegistry
from src.contexts.shared_kernel.time_provider import FakeTimeProvider, SystemTimeProvider
from src.contexts.shared_kernel.timestamp import Timestamp
from src.infrastructure.outbox import OutboxRelay
from src.infrastructure.outbox.publishers import RegisterUserOutbox

pytestmark = pytest.mark.asyncio

_REGISTERED_AT = 1798221600


@pytest_asyncio.fixture
async def clean_identity(postgres_engine: AsyncEngine) -> AsyncGenerator[AsyncEngine]:
    """Leere Nutzer und Outbox vor und nach jedem Test."""
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users CASCADE"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))
    yield postgres_engine
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users CASCADE"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))


def _request(**overrides: str) -> RegisterUserRequest:
    """Baue einen gueltigen Registrierungs-Request, feldweise ueberschreibbar."""
    return RegisterUserRequest(
        **{
            "email": "markus@example.de",
            "password": "ein-langes-passwort",
            "display_name": "Markus",
            "locale": "de",
            "time_zone_id": "Europe/Berlin",
            **overrides,
        }
    )


async def _register(connection: AsyncConnection, request: RegisterUserRequest) -> object:
    """Fuehre den Use Case gegen echte Infrastruktur in der gegebenen Transaktion aus.

    Dieselbe Fabrik wie die Produktion und wie die Test-API - getauscht wird
    ausschliesslich, was hinter der Naht steckt. `PostgresUserStore` und
    `RegisterUserOutbox` bekommen **dieselbe** Verbindung; genau daran haengt
    die transaktionale Kopplung, die dieser Test prueft.
    """
    pipeline = build_register_user_pipeline(
        store=PostgresUserStore(connection),
        hasher=Argon2PasswordHasher(),
        labels=IdnaLabels(),
        events=RegisterUserOutbox(connection),
        sessions=PostgresSessionTokens(connection, JwtAccessTokens("t" * 32)),
        clock=FakeTimeProvider(Timestamp(_REGISTERED_AT).to_datetime()),
        tokens=FixedTokenOptions(),
    )
    return await pipeline.run(request)


async def _counts(engine: AsyncEngine) -> tuple[int, int]:
    """Zaehle Nutzer- und Outbox-Zeilen."""
    async with engine.begin() as connection:
        users = await connection.scalar(text("SELECT count(*) FROM identity.users"))
        events = await connection.scalar(text("SELECT count(*) FROM shared_kernel.outbox"))
    return int(users or 0), int(events or 0)


async def test_nutzer_und_ereignis_entstehen_gemeinsam(clean_identity: AsyncEngine) -> None:
    """Ein Commit macht beide Zeilen sichtbar."""
    async with clean_identity.connect() as connection:
        await connection.begin()
        result = await _register(connection, _request())
        await connection.commit()

    assert isinstance(result, RegistrationAccepted)
    assert await _counts(clean_identity) == (1, 1)


async def test_ohne_commit_entsteht_keine_von_beiden(clean_identity: AsyncEngine) -> None:
    """Der zurueckgenommene Vorgang hinterlaesst auch kein Ereignis.

    Das ist der Ausgang, den die Outbox verhindert: ein Ereignis, das eine
    Registrierung meldet, die es nie gegeben hat.
    """
    async with clean_identity.connect() as connection:
        await connection.begin()
        result = await _register(connection, _request())
        await connection.rollback()

    assert isinstance(result, RegistrationAccepted)
    assert await _counts(clean_identity) == (0, 0)


async def test_der_unique_constraint_entscheidet_die_eindeutigkeit(
    clean_identity: AsyncEngine,
) -> None:
    async with clean_identity.connect() as connection:
        await connection.begin()
        await _register(connection, _request())
        await connection.commit()

    async with clean_identity.connect() as connection:
        await connection.begin()
        result = await _register(connection, _request(display_name="Jemand anderes"))
        await connection.commit()

    assert isinstance(result, EmailAlreadyTaken)
    assert result.email == "markus@example.de"
    # Kein zweiter Nutzer - und vor allem kein zweites Ereignis: eine abgelehnte
    # Registrierung ist nichts, worauf ein anderer Context reagieren duerfte.
    assert await _counts(clean_identity) == (1, 1)


async def test_die_adresse_ist_unabhaengig_von_der_schreibweise_vergeben(
    clean_identity: AsyncEngine,
) -> None:
    """Normalisiert wird vor dem Schreiben, nicht im Index."""
    async with clean_identity.connect() as connection:
        await connection.begin()
        await _register(connection, _request(email="markus@example.de"))
        await connection.commit()

    async with clean_identity.connect() as connection:
        await connection.begin()
        result = await _register(connection, _request(email="MARKUS@Example.DE"))
        await connection.commit()

    assert isinstance(result, EmailAlreadyTaken)


async def test_gespeichert_wird_ein_echter_argon2id_hash(clean_identity: AsyncEngine) -> None:
    """Im Feld steht ein PHC-String, der das Passwort verifiziert - kein Klartext."""
    async with clean_identity.connect() as connection:
        await connection.begin()
        await _register(connection, _request(password="ein-langes-passwort"))
        await connection.commit()

    async with clean_identity.begin() as connection:
        stored = await connection.scalar(text("SELECT password_hash FROM identity.users"))

    assert stored is not None
    assert stored.startswith("$argon2id$")
    assert "ein-langes-passwort" not in stored
    assert Argon2().verify(stored, "ein-langes-passwort")


async def test_das_ereignis_erreicht_einen_registrierten_handler(
    clean_identity: AsyncEngine,
) -> None:
    """Die ganze Kette: Handler meldet, Outbox haelt fest, Relay stellt zu.

    Registriert wird ueber den Vertragstyp `UserRegistered` - derselbe Typ, den
    Goals und Diary spaeter importieren werden. Damit prueft dieser Test auch,
    dass der Name, unter dem geschrieben wird, und der, unter dem nachgeschlagen
    wird, tatsaechlich derselbe sind.
    """
    delivered: list[DeliveredEvent] = []

    class CollectingHandler:
        async def handle(self, event: DeliveredEvent) -> None:
            delivered.append(event)

    registry = EventRegistry()
    registry.register(UserRegistered, CollectingHandler())

    async with clean_identity.connect() as connection:
        await connection.begin()
        result = await _register(connection, _request())
        await connection.commit()

    assert isinstance(result, RegistrationAccepted)
    assert await OutboxRelay(clean_identity, registry, SystemTimeProvider()).relay_due_events() == 1

    (announced,) = delivered
    assert announced.event_type == UserRegistered.EVENT_TYPE
    assert announced.occurred_at == Timestamp(_REGISTERED_AT)
    assert announced.payload == {
        "userId": result.user_id,
        "email": "markus@example.de",
        "locale": "de",
        "timeZoneId": "Europe/Berlin",
        "registeredAt": _REGISTERED_AT,
    }
