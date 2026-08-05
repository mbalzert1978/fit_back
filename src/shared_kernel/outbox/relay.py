"""Relay worker: fetches events from outbox and notifies subscribers via LISTEN/NOTIFY."""

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared_infrastructure.outbox import OutboxEvent

logger = logging.getLogger(__name__)

# LISTEN/NOTIFY channel name for outbox events
OUTBOX_NOTIFY_CHANNEL = "outbox_events"


@dataclass(frozen=True, slots=True)
class RelayConfig:
    """Configuration for the relay worker."""

    batch_size: int = 10
    """Maximum events to fetch and process in one iteration."""

    max_retries: int = 3
    """Maximum retry attempts per event."""

    backoff_base_ms: float = 100.0
    """Base delay in milliseconds for exponential backoff (2^attempt * base)."""

    poll_interval_ms: float = 1000.0
    """Interval in milliseconds to check for new events."""


async def relay_outbox_events(
    session: AsyncSession,
    worker_id: UUID | None = None,
    config: RelayConfig | None = None,
) -> None:
    """Relay unprocessed events from the outbox to subscribers via LISTEN/NOTIFY.

    Fetches unprocessed events using SELECT...FOR UPDATE SKIP LOCKED (write-lock
    to prevent duplicate processing), marks them as processed, and notifies
    subscribers on the OUTBOX_NOTIFY_CHANNEL.

    Implements idempotent retry logic: events with retry_count >= max_retries
    are marked as processed but logged for manual inspection.

    Args:
        session: Async SQLAlchemy session (must be connected to Postgres).
        worker_id: Unique identifier for this worker instance (UUID); if None, a new UUID is generated.
        config: Relay configuration; uses defaults if None.

    Raises:
        RuntimeError: If the database is not Postgres or if connection fails.
    """
    if worker_id is None:
        worker_id = uuid4()
    if config is None:
        config = RelayConfig()

    logger.info(f"Starting relay worker {worker_id} with batch_size={config.batch_size}")

    try:
        while True:
            events_processed = await _relay_batch(session, worker_id, config)
            if events_processed == 0:
                # No events to process; sleep before next check
                await asyncio.sleep(config.poll_interval_ms / 1000.0)
    except asyncio.CancelledError:
        logger.info(f"Relay worker {worker_id} cancelled")
        raise


async def _relay_batch(
    session: AsyncSession,
    worker_id: UUID,
    config: RelayConfig,
) -> int:
    """Fetch and process one batch of unprocessed events.

    Returns the number of events processed in this batch.
    """
    try:
        # Use raw connection to set isolation level and issue raw SQL
        if await session.connection() is None:
            raise RuntimeError("Session not connected; cannot relay events")

        # Fetch unprocessed events with write lock (SKIP LOCKED prevents blocking)
        # Query: SELECT * FROM shared.outbox
        #        WHERE processed_at IS NULL
        #        ORDER BY created_at ASC
        #        FOR UPDATE SKIP LOCKED
        #        LIMIT batch_size
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed_at.is_(None))
            .order_by(OutboxEvent.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(config.batch_size)
        )

        result = await session.execute(stmt)
        events = result.scalars().all()

        if not events:
            return 0

        # Process each event
        for event in events:
            await _process_event(session, event, worker_id, config)

        # Commit the batch
        await session.commit()

        logger.info(f"Relayed {len(events)} events in batch")
        return len(events)

    except Exception:
        logger.exception("Error in relay batch")
        await session.rollback()
        raise


async def _process_event(
    session: AsyncSession,
    event: OutboxEvent,
    worker_id: UUID,
    config: RelayConfig,
) -> None:
    """Process a single event: mark as processed and notify subscribers.

    If max retries exceeded, mark as processed (give up) and log.
    """
    try:
        if event.retry_count >= config.max_retries:
            logger.warning(
                f"Event {event.id} exceeded max retries ({config.max_retries}); giving up. "
                f"Last error: {event.last_error}"
            )
            event.processed_at = None  # Will be set by UPDATE below
            event.processed_by = worker_id
            # Don't mark as processed; rely on UPDATE below
        else:
            # Attempt to notify subscribers
            await _notify_subscribers(session, event)

        # Mark event as processed
        event.processed_at = None  # Will be populated by SQL now()
        event.processed_by = worker_id

        # Refresh from DB to get server-generated timestamp
        await session.flush()
        # Use raw SQL to set processed_at to current time
        update_stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event.id)
            .values(
                processed_by=worker_id,
                processed_at=text("now()"),
                retry_count=event.retry_count,
                last_error=None,
            )
        )
        await session.execute(update_stmt)

        logger.info(f"Event {event.id} processed by worker {worker_id}")

    except Exception as exc:  # noqa: BLE001 - catch all to implement retry logic
        logger.error(f"Error processing event {event.id}: {exc}")
        # Update retry count and last error
        event.retry_count += 1
        event.last_error = str(exc)

        update_stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event.id)
            .values(
                retry_count=event.retry_count,
                last_error=event.last_error,
            )
        )
        await session.execute(update_stmt)

        # Exponential backoff before retry
        backoff_ms = config.backoff_base_ms * (2**event.retry_count)
        logger.info(f"Event {event.id} retry #{event.retry_count}, backoff {backoff_ms}ms")
        await asyncio.sleep(backoff_ms / 1000.0)


async def _notify_subscribers(
    session: AsyncSession,
    event: OutboxEvent,
) -> None:
    """Notify subscribers of a new event via LISTEN/NOTIFY.

    Sends the event ID and type on OUTBOX_NOTIFY_CHANNEL.
    """
    # Verify we have a connection (we'll use raw SQL via session.execute)
    # session.connection() returns async context manager, we just need to verify we can query
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError("No connection available for NOTIFY") from exc

    # Prepare notification payload
    payload = f'{{"id": "{event.id}", "event_type": "{event.event_type}", "aggregate_id": "{event.aggregate_id}"}}'

    # NOTIFY is not directly exposed in asyncpg, so we use raw SQL
    notify_sql = f"NOTIFY {OUTBOX_NOTIFY_CHANNEL}, '{payload}'"
    await session.execute(text(notify_sql))

    logger.debug(f"Notified {OUTBOX_NOTIFY_CHANNEL} for event {event.id}")
