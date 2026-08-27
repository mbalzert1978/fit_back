"""Integrationstests der Postgres-Outbox gegen eine echte Datenbank.

Echtes Postgres statt Fakes, weil hier ausschliesslich Postgres-Verhalten
geprueft wird: `FOR UPDATE SKIP LOCKED`, transaktionales `pg_notify`, Sperren
ueber nebenlaeufige Transaktionen. Ein Fake davon waere die Spezifikation gegen
sich selbst geprueft - er koennte nur bestaetigen, was wir ihm beigebracht haben.
"""

import asyncio
from collections.abc import AsyncGenerator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar, final

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.contexts.shared_kernel.events import DeliveredEvent, EventRegistry, JsonValue
from src.contexts.shared_kernel.time_provider import FakeTimeProvider
from src.contexts.shared_kernel.timestamp import Timestamp
from src.infrastructure.outbox import OutboxRelay, OutboxWorker, RelayConfig, write_event

pytestmark = pytest.mark.asyncio


@final
@dataclass(frozen=True, slots=True)
class DummyAggregateChanged:
    """Ein veroeffentlichtes Ereignis ohne Fachlichkeit - Traeger fuer den Mechanismus.

    Bewusst hier und nicht aus einem Context geliehen: geprueft wird der
    Transport, nicht die Fachlichkeit irgendeiner Domaene. Ein echtes Ereignis
    wuerde diese Tests an einen Context binden, den sie nichts angehen.
    """

    EVENT_TYPE: ClassVar[str] = "DummyAggregateChanged"

    index: int
    occurred_at: Timestamp

    def to_payload(self) -> Mapping[str, JsonValue]:
        return {"index": self.index}


class RecordingHandler:
    """Test-Consumer: haelt fest, was ihm zugestellt wurde."""

    def __init__(self) -> None:
        self.delivered: list[DeliveredEvent] = []

    async def handle(self, event: DeliveredEvent) -> None:
        self.delivered.append(event)


class FailingHandler:
    """Test-Consumer, der die ersten `failures` Zustellungen ablehnt."""

    def __init__(self, failures: int) -> None:
        """Lege fest, wie oft der Handler scheitert, bevor er annimmt."""
        self._remaining = failures
        self.calls = 0

    async def handle(self, _event: DeliveredEvent) -> None:
        """Scheitere, solange noch Fehlversuche uebrig sind."""
        self.calls += 1
        if self._remaining > 0:
            self._remaining -= 1
            msg = "Consumer nicht bereit"
            raise RuntimeError(msg)


@pytest_asyncio.fixture
async def clean_outbox(postgres_engine: AsyncEngine) -> AsyncGenerator[AsyncEngine]:
    """Leere die Outbox vor und nach jedem Test."""
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))
    yield postgres_engine
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))


def _index_of(event: DeliveredEvent) -> int:
    """Lies den `index` einer Zustellung heraus - in diesen Tests immer eine Zahl.

    Die Nutzlast ist auf der Leitung nur `JsonValue`; erst hier steht wieder fest,
    dass darin die Zahl steckt, die `DummyAggregateChanged` hineingeschrieben hat.
    """
    index = event.payload["index"]
    assert isinstance(index, int), f"index ist keine Zahl: {index!r}"
    return index


def _clock_at(unix_seconds: int) -> FakeTimeProvider:
    return FakeTimeProvider(datetime.fromtimestamp(unix_seconds, UTC))


def _relay(
    engine: AsyncEngine,
    registry: EventRegistry,
    unix_seconds: int = 1_000_000,
    config: RelayConfig | None = None,
) -> OutboxRelay:
    return OutboxRelay(engine, registry, _clock_at(unix_seconds), config)


async def _publish(engine: AsyncEngine, index: int = 0, *, commit: bool = True) -> None:
    """Schreibe ein Event - wahlweise mit oder ohne Commit der umgebenden Transaktion."""
    event = DummyAggregateChanged(index=index, occurred_at=Timestamp(1_000_000))
    async with engine.connect() as connection:
        await connection.begin()
        await write_event(
            connection,
            event.EVENT_TYPE,
            event.to_payload(),
            event.occurred_at,
        )
        if commit:
            await connection.commit()
        else:
            await connection.rollback()


async def test_event_ohne_commit_wird_nie_zugestellt(clean_outbox: AsyncEngine) -> None:
    """Der Aggregate-Write entscheidet ueber das Event, nicht der Schreibvorgang selbst."""
    handler = RecordingHandler()
    registry = EventRegistry()
    registry.register(DummyAggregateChanged, handler)

    await _publish(clean_outbox, commit=False)

    assert await _relay(clean_outbox, registry).relay_due_events() == 0
    assert handler.delivered == []


async def test_committetes_event_wird_genau_einmal_zugestellt(clean_outbox: AsyncEngine) -> None:
    """AC1: ein transaktional geschriebenes Event erreicht den Consumer, und zwar einmal."""
    handler = RecordingHandler()
    registry = EventRegistry()
    registry.register(DummyAggregateChanged, handler)

    await _publish(clean_outbox, index=7)

    relay = _relay(clean_outbox, registry)
    assert await relay.relay_due_events() == 1
    # Zweiter Durchlauf: die Zeile ist als verarbeitet markiert und faellt aus
    # der Claim-Query heraus - sonst wuerde jeder Lauf erneut zustellen.
    assert await relay.relay_due_events() == 0

    assert len(handler.delivered) == 1
    delivered = handler.delivered[0]
    assert delivered.event_type == DummyAggregateChanged.EVENT_TYPE
    assert delivered.payload == {"index": 7}
    assert delivered.occurred_at == Timestamp(1_000_000)
    assert delivered.attempt == 1


async def test_nebenlaeufige_relays_verarbeiten_kein_event_doppelt(
    clean_outbox: AsyncEngine,
) -> None:
    """AC2: `SKIP LOCKED` greift nachweislich.

    Die Barriere ist der eigentliche Beweis: beide Handler kommen nur dann
    gemeinsam durch, wenn beide Transaktionen **gleichzeitig** offen sind. Ohne
    `SKIP LOCKED` wuerde der zweite Relay auf der gesperrten Zeile warten, die
    Barriere nie erreicht und der Test in den Timeout laufen.
    """
    barrier = asyncio.Barrier(2)

    class BarrierHandler(RecordingHandler):
        async def handle(self, event: DeliveredEvent) -> None:
            await barrier.wait()
            await super().handle(event)

    first, second = BarrierHandler(), BarrierHandler()
    registries = []
    for handler in (first, second):
        registry = EventRegistry()
        registry.register(DummyAggregateChanged, handler)
        registries.append(registry)

    await _publish(clean_outbox, index=1)
    await _publish(clean_outbox, index=2)

    # batch_size=1, damit sich beide Relays je eine der beiden Zeilen greifen -
    # mit einem groesseren Batch naehme der erste beide und der zweite haette
    # nichts zu ueberspringen.
    config = RelayConfig(batch_size=1)
    async with asyncio.timeout(15):
        claimed = await asyncio.gather(
            _relay(clean_outbox, registries[0], config=config).relay_due_events(),
            _relay(clean_outbox, registries[1], config=config).relay_due_events(),
        )

    assert claimed == [1, 1]
    indices = [_index_of(event) for event in (*first.delivered, *second.delivered)]
    assert sorted(indices) == [1, 2]


async def test_worker_stellt_ohne_polling_intervall_zu(clean_outbox: AsyncEngine) -> None:
    """AC3: die Zustellung haengt an LISTEN/NOTIFY, nicht am Polling.

    `idle_wait_seconds` steht auf einer Stunde. Kaeme das Event trotzdem in
    Sekunden an, kann es nur die Benachrichtigung gewesen sein.
    """
    delivered = asyncio.Event()

    class SignallingHandler(RecordingHandler):
        async def handle(self, event: DeliveredEvent) -> None:
            await super().handle(event)
            delivered.set()

    handler = SignallingHandler()
    registry = EventRegistry()
    registry.register(DummyAggregateChanged, handler)

    worker = OutboxWorker(
        clean_outbox,
        _relay(clean_outbox, registry),
        idle_wait_seconds=3600.0,
    )
    running = asyncio.create_task(worker.run())
    try:
        # Ohne bestehendes LISTEN ginge die Benachrichtigung ins Leere und der
        # Worker schliefe die volle Stunde. Kein Zustand verraet von aussen,
        # wann die Verbindung lauscht - daher diese kurze Anlaufzeit.
        await asyncio.sleep(1.0)
        await _publish(clean_outbox, index=42)

        async with asyncio.timeout(10):
            await delivered.wait()
    finally:
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running

    assert [event.payload["index"] for event in handler.delivered] == [42]


async def test_fehlschlag_verschiebt_die_faelligkeit_statt_zu_warten(
    clean_outbox: AsyncEngine,
) -> None:
    handler = FailingHandler(failures=1)
    registry = EventRegistry()
    registry.register(DummyAggregateChanged, handler)

    await _publish(clean_outbox)

    now = 1_000_000
    assert await _relay(clean_outbox, registry, now).relay_due_events() == 1
    assert handler.calls == 1

    async with clean_outbox.begin() as connection:
        row = (
            (
                await connection.execute(
                    text(
                        "SELECT attempts, next_attempt_at, processed_at, failed_at, last_error "
                        "FROM shared_kernel.outbox"
                    )
                )
            )
            .mappings()
            .one()
        )
    assert row["attempts"] == 1
    assert row["processed_at"] is None
    assert row["failed_at"] is None
    assert row["next_attempt_at"] == now + 1
    assert "Consumer nicht bereit" in row["last_error"]

    # Zur selben Sekunde ist nichts faellig; eine Sekunde spaeter schon.
    assert await _relay(clean_outbox, registry, now).relay_due_events() == 0
    assert await _relay(clean_outbox, registry, now + 1).relay_due_events() == 1
    assert handler.calls == 2

    async with clean_outbox.begin() as connection:
        processed_at = await connection.scalar(
            text("SELECT processed_at FROM shared_kernel.outbox")
        )
    assert processed_at == now + 1


async def test_aufgegebenes_event_gilt_nicht_als_zugestellt(clean_outbox: AsyncEngine) -> None:
    """Nach erschoepften Versuchen wird `failed_at` gesetzt - `processed_at` bleibt leer."""
    handler = FailingHandler(failures=10)
    registry = EventRegistry()
    registry.register(DummyAggregateChanged, handler)

    await _publish(clean_outbox)

    config = RelayConfig(max_attempts=3)
    now = 1_000_000
    for attempt in range(3):
        # Die Uhr muss ueber den Backoff hinweg vorruecken, sonst ist die Zeile
        # beim naechsten Durchlauf schlicht noch nicht wieder faellig.
        assert await _relay(clean_outbox, registry, now, config).relay_due_events() == 1
        now += 2 ** (attempt + 1)

    assert handler.calls == 3

    async with clean_outbox.begin() as connection:
        row = (
            (
                await connection.execute(
                    text("SELECT attempts, processed_at, failed_at FROM shared_kernel.outbox")
                )
            )
            .mappings()
            .one()
        )
    assert row["attempts"] == 3
    assert row["failed_at"] is not None
    assert row["processed_at"] is None

    assert await _relay(clean_outbox, registry, now + 3600, config).relay_due_events() == 0


async def test_event_ohne_registrierten_handler_gilt_als_erledigt(
    clean_outbox: AsyncEngine,
) -> None:
    """Ein Context veroeffentlicht, was passiert ist - ob jemand zuhoert, ist nicht seine Frage."""
    await _publish(clean_outbox)

    relay = _relay(clean_outbox, EventRegistry())
    assert await relay.relay_due_events() == 1
    assert await relay.relay_due_events() == 0


async def test_ein_ereignis_aus_der_zukunft_ist_trotzdem_sofort_faellig(
    clean_outbox: AsyncEngine,
) -> None:
    """`occurred_at` ist ein fachlicher Zeitpunkt, kein Zustelltermin.

    Geht die Uhr des schreibenden Context vor - oder traegt ein Ereignis
    absichtlich ein spaeteres Datum -, darf die Zeile nicht liegenbleiben, bis
    die Wanduhr aufgeholt hat. Genau das passierte, solange `next_attempt_at`
    mit `occurred_at` initialisiert wurde.
    """
    handler = RecordingHandler()
    registry = EventRegistry()
    registry.register(DummyAggregateChanged, handler)

    weit_in_der_zukunft = Timestamp(4_000_000_000)
    async with clean_outbox.begin() as connection:
        await write_event(
            connection, DummyAggregateChanged.EVENT_TYPE, {"index": 1}, weit_in_der_zukunft
        )

    relay_uhr_steht_frueher = 1_000_000
    assert await _relay(clean_outbox, registry, relay_uhr_steht_frueher).relay_due_events() == 1
    assert handler.delivered[0].occurred_at == weit_in_der_zukunft
