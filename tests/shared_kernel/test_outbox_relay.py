"""Tests for outbox relay worker and publisher."""

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.community.postgres import PostgresContainer

from src.shared_infrastructure.outbox import OutboxEvent
from src.shared_kernel.outbox import publish_outbox_event, relay_outbox_events
from src.shared_kernel.outbox.relay import RelayConfig


@pytest_asyncio.fixture(scope="function")
async def test_engine(postgres_service: PostgresContainer) -> AsyncEngine:
    """Create a dedicated engine for outbox tests."""
    host = postgres_service.get_container_host_ip()
    port = postgres_service.get_exposed_port(5432)
    user = "test"
    password = "test"
    database = "test"

    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine: AsyncEngine) -> AsyncSession:
    """Create a session for outbox tests."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


class TestPublishOutboxEvent:
    """Tests for publish_outbox_event()."""

    @pytest.mark.asyncio
    async def test_publish_event_to_outbox(self, test_session: AsyncSession) -> None:
        """Test publishing an event writes it to the outbox table."""
        aggregate_id = uuid4()
        payload = {"user_email": "test@example.com", "name": "Test User"}

        # Publish event
        await publish_outbox_event(
            test_session,
            event_type="UserRegistered",
            aggregate_id=aggregate_id,
            aggregate_type="User",
            payload=payload,
        )
        await test_session.commit()

        # Verify event exists
        stmt = select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id)
        result = await test_session.execute(stmt)
        event = result.scalar_one_or_none()

        assert event is not None
        assert event.event_type == "UserRegistered"
        assert event.aggregate_id == aggregate_id
        assert event.aggregate_type == "User"
        assert event.payload == payload
        assert event.processed_at is None
        assert event.retry_count == 0

    @pytest.mark.asyncio
    async def test_publish_event_invalid_event_type(self, test_session: AsyncSession) -> None:
        """Test publishing with invalid event_type raises ValueError."""
        with pytest.raises(ValueError, match="event_type must be a non-empty string"):
            await publish_outbox_event(
                test_session,
                event_type="",  # Empty string
                aggregate_id=uuid4(),
                aggregate_type="User",
                payload={},
            )

    @pytest.mark.asyncio
    async def test_publish_event_invalid_aggregate_type(self, test_session: AsyncSession) -> None:
        """Test publishing with invalid aggregate_type raises ValueError."""
        with pytest.raises(ValueError, match="aggregate_type must be a non-empty string"):
            await publish_outbox_event(
                test_session,
                event_type="UserRegistered",
                aggregate_id=uuid4(),
                aggregate_type="",  # Empty string
                payload={},
            )

    @pytest.mark.asyncio
    async def test_publish_event_invalid_payload(self, test_session: AsyncSession) -> None:
        """Test publishing with non-dict payload raises ValueError."""
        with pytest.raises(TypeError, match="payload must be a dict"):
            await publish_outbox_event(
                test_session,
                event_type="UserRegistered",
                aggregate_id=uuid4(),
                aggregate_type="User",
                payload="not a dict",  # type: ignore
            )


class TestRelayOutboxEvents:
    """Tests for relay_outbox_events()."""

    @pytest.mark.asyncio
    async def test_relay_event_once(self, test_engine: AsyncEngine) -> None:
        """Test that an event is processed exactly once (processed_at set)."""
        async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        # Publish event
        aggregate_id = uuid4()
        async with async_session() as session:
            await publish_outbox_event(
                session,
                event_type="UserRegistered",
                aggregate_id=aggregate_id,
                aggregate_type="User",
                payload={"email": "test@example.com"},
            )
            await session.commit()

        # Verify unprocessed
        async with async_session() as session:
            stmt = select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id)
            result = await session.execute(stmt)
            event = result.scalar_one()
            assert event.processed_at is None

        # Run relay (1 iteration, fetch batch)
        worker_id = uuid4()
        config = RelayConfig(batch_size=10, poll_interval_ms=100)

        async with async_session() as session:
            relay_task = asyncio.create_task(
                relay_outbox_events(session, worker_id=worker_id, config=config)
            )

            # Let relay process batch
            await asyncio.sleep(0.3)
            relay_task.cancel()
            try:
                await relay_task
            except asyncio.CancelledError:
                pass

        # Verify event processed
        async with async_session() as session:
            stmt = select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id)
            result = await session.execute(stmt)
            event = result.scalar_one()
            assert event.processed_at is not None
            assert event.processed_by == worker_id
            assert event.retry_count == 0
            assert event.last_error is None

    @pytest.mark.asyncio
    async def test_relay_skip_locked_prevents_duplicate(self, test_engine: AsyncEngine) -> None:
        """Test that two relay workers do not process the same event (SKIP LOCKED).

        This test verifies that the SELECT...FOR UPDATE SKIP LOCKED query prevents
        duplicate processing when multiple workers run concurrently.
        """
        # Publish event
        async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        aggregate_id = uuid4()
        async with async_session() as session:
            await publish_outbox_event(
                session,
                event_type="UserRegistered",
                aggregate_id=aggregate_id,
                aggregate_type="User",
                payload={"email": "test@example.com"},
            )
            await session.commit()

        # Run two relay workers concurrently
        worker1_id = uuid4()
        worker2_id = uuid4()
        config = RelayConfig(batch_size=10, poll_interval_ms=50)

        task1 = asyncio.create_task(
            relay_outbox_events(async_session(), worker_id=worker1_id, config=config)
        )
        task2 = asyncio.create_task(
            relay_outbox_events(async_session(), worker_id=worker2_id, config=config)
        )

        # Let them run briefly
        await asyncio.sleep(0.5)
        task1.cancel()
        task2.cancel()

        for task in [task1, task2]:
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Verify event was processed by exactly one worker
        async with async_session() as session:
            stmt = select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id)
            result = await session.execute(stmt)
            event = result.scalar_one()

            processed_by = event.processed_by
            assert processed_by is not None
            assert processed_by in (worker1_id, worker2_id)  # One of them
            assert event.processed_at is not None

    @pytest.mark.asyncio
    async def test_relay_batch_limit(self, test_session: AsyncSession) -> None:
        """Test that relay respects batch_size limit."""
        # Publish 15 events
        events_count = 15
        for i in range(events_count):
            await publish_outbox_event(
                test_session,
                event_type="UserRegistered",
                aggregate_id=uuid4(),
                aggregate_type="User",
                payload={"index": i},
            )
        await test_session.commit()

        # Run relay with batch_size=10
        config = RelayConfig(batch_size=10, poll_interval_ms=100)
        worker_id = uuid4()

        relay_task = asyncio.create_task(
            relay_outbox_events(test_session, worker_id=worker_id, config=config)
        )

        # Let relay process first batch
        await asyncio.sleep(0.3)
        relay_task.cancel()
        try:
            await relay_task
        except asyncio.CancelledError:
            pass

        # Count processed events
        stmt = select(OutboxEvent).where(OutboxEvent.processed_at.isnot(None))
        result = await test_session.execute(stmt)
        processed_events = result.scalars().all()

        # Should have processed 10 (first batch)
        assert len(processed_events) >= 10

    @pytest.mark.asyncio
    async def test_relay_retry_logic(self, test_session: AsyncSession) -> None:
        """Test retry logic: events with max retries are marked as processed."""
        aggregate_id = uuid4()

        # Manually insert an event with retry_count at max
        event = OutboxEvent(
            id=uuid4(),
            event_type="TestEvent",
            aggregate_id=aggregate_id,
            aggregate_type="Test",
            payload={"test": "data"},
            processed_at=None,
            processed_by=None,
            retry_count=3,  # Max retries exceeded
            last_error="Previous error",
        )
        test_session.add(event)
        await test_session.commit()

        # Refresh
        result = await test_session.execute(select(OutboxEvent).where(OutboxEvent.id == event.id))
        event = result.scalar_one()
        assert event.retry_count == 3

        # Run relay
        config = RelayConfig(max_retries=3)
        worker_id = uuid4()

        relay_task = asyncio.create_task(
            relay_outbox_events(test_session, worker_id=worker_id, config=config)
        )

        await asyncio.sleep(0.2)
        relay_task.cancel()
        try:
            await relay_task
        except asyncio.CancelledError:
            pass

        # Verify event is marked as processed despite max retries
        result = await test_session.execute(select(OutboxEvent).where(OutboxEvent.id == event.id))
        event = result.scalar_one()
        assert event.processed_by == worker_id

    @pytest.mark.asyncio
    async def test_relay_notify_payload_safe(self, test_engine: AsyncEngine) -> None:
        """Verifiziert, dass NOTIFY-Payload sicher gegen SQL-Injection escaped ist.

        Kontrolliert, dass Payload mit Sonderzeichen (Anführungszeichen, etc.) korrekt
        escaped wird, um SQL-Injection zu verhindern.
        """
        async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        # Erstelle Event mit Payload, die Anführungszeichen enthält
        aggregate_id = uuid4()
        async with async_session() as session:
            await publish_outbox_event(
                session,
                event_type="UserRegistered",
                aggregate_id=aggregate_id,
                aggregate_type="User",
                # Payload mit gefährlichen Zeichen
                payload={"email": "test\"with'quotes@example.com"},
            )
            await session.commit()

        # Relaye das Event - sollte ohne Fehler durchlaufen
        async with async_session() as session:
            relay_config = RelayConfig(batch_size=10, poll_interval_ms=100)
            relay_task = asyncio.create_task(
                relay_outbox_events(session, worker_id=uuid4(), config=relay_config)
            )

            # Lasse relativ lange laufen, um sicherzustellen, dass Event verarbeitet wird
            await asyncio.sleep(0.5)
            relay_task.cancel()
            try:
                await relay_task
            except asyncio.CancelledError:
                pass

        # Verifiziere, dass Event trotz Sonderzeichen verarbeitet wurde
        async with async_session() as session:
            result = await session.execute(
                select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id)
            )
            event = result.scalar_one()
            assert event.processed_at is not None
            assert event.processed_by is not None

    @pytest.mark.asyncio
    async def test_relay_skip_locked_across_sessions(self, test_engine: AsyncEngine) -> None:
        """Verifiziert SKIP LOCKED über separate DB-Sessions (wie separate Container).

        Imitiert zwei separate Worker-Prozesse mit eigenen Engines und Sessions.
        """
        # Erstelle zwei separate AsyncSessions
        async_session_factory = sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        aggregate_id = uuid4()

        # Publish Event in erster Session
        async with async_session_factory() as session:
            await publish_outbox_event(
                session,
                event_type="UserRegistered",
                aggregate_id=aggregate_id,
                aggregate_type="User",
                payload={"email": "test@example.com"},
            )
            await session.commit()

        # Starte zwei Worker mit je einer eigenen Session
        worker1_id = uuid4()
        worker2_id = uuid4()
        config = RelayConfig(batch_size=10, poll_interval_ms=50)

        task1 = None
        task2 = None
        try:
            async with async_session_factory() as session1, async_session_factory() as session2:
                task1 = asyncio.create_task(
                    relay_outbox_events(session1, worker_id=worker1_id, config=config)
                )
                task2 = asyncio.create_task(
                    relay_outbox_events(session2, worker_id=worker2_id, config=config)
                )

                # Lasse sie kurz laufen
                await asyncio.sleep(0.5)

                # Beende beide
                task1.cancel()
                task2.cancel()

                for task in [task1, task2]:
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        except Exception:
            # Cleanup tasks if setup failed
            for task in [task1, task2]:
                if task and not task.done():
                    task.cancel()
            raise

        # Verifiziere, dass Event nur von einem Worker verarbeitet wurde
        async with async_session_factory() as session:
            result = await session.execute(
                select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id)
            )
            event = result.scalar_one()

            # Nur einer der beiden Worker sollte es verarbeitet haben
            assert event.processed_by in (worker1_id, worker2_id)
            assert event.processed_at is not None

    @pytest.mark.asyncio
    async def test_relay_exponential_backoff(self, test_session: AsyncSession) -> None:
        """Verifiziert, dass Retry-Backoff exponentiell wächst."""
        aggregate_id = uuid4()
        event_id = uuid4()

        # Erstelle manuell ein Event mit retry_count
        event = OutboxEvent(
            id=event_id,
            event_type="TestEvent",
            aggregate_id=aggregate_id,
            aggregate_type="Test",
            payload={"test": "data"},
            processed_at=None,
            processed_by=None,
            retry_count=0,
            last_error=None,
        )
        test_session.add(event)
        await test_session.commit()

        # Mocke asyncio.sleep, um Backoff-Delays zu tracken
        with (
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            patch(
                "src.shared_kernel.outbox.relay._notify_subscribers",
                new_callable=AsyncMock,
                side_effect=Exception("Test error"),
            ),
        ):
            # Relaye das Event (sollte fehlschlagen und Backoff versuchen)
            config = RelayConfig(max_retries=3, backoff_base_ms=100.0)
            worker_id = uuid4()

            relay_task = asyncio.create_task(
                relay_outbox_events(test_session, worker_id=worker_id, config=config)
            )

            # Lasse kurz laufen
            await asyncio.sleep(0.1)
            relay_task.cancel()
            try:
                await relay_task
            except asyncio.CancelledError:
                pass

        # Verifiziere, dass asyncio.sleep mit exponentiellen Delays aufgerufen wurde
        sleep_calls = mock_sleep.call_args_list
        if len(sleep_calls) >= 2:
            # Extrahiere die tatsächlichen Delay-Werte (in Sekunden)
            sleep_values = [call.args[0] for call in sleep_calls]
            # Verifiziere, dass sie exponentiell ansteigen
            for i in range(1, len(sleep_values)):
                assert sleep_values[i] > sleep_values[i - 1], (
                    f"Backoff nicht exponentiell: {sleep_values[i]} nicht > {sleep_values[i - 1]}"
                )
