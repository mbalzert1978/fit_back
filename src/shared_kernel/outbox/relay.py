"""Relay worker: fetches events from outbox and notifies subscribers via LISTEN/NOTIFY."""

import asyncio
import json
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
    """Konfiguration für den Relay-Worker."""

    batch_size: int = 10
    """Maximale Anzahl von Events, die in einer Iteration geholt und verarbeitet werden."""

    max_retries: int = 3
    """Maximale Retry-Versuche pro Event."""

    backoff_base_ms: float = 100.0
    """Basisverzögerung in Millisekunden für exponentiellen Backoff (2^attempt * base)."""

    poll_interval_ms: float = 1000.0
    """Intervall in Millisekunden zum Prüfen auf neue Events."""


async def relay_outbox_events(
    session: AsyncSession,
    worker_id: UUID | None = None,
    config: RelayConfig | None = None,
) -> None:
    """Leite unverarbeitete Events aus der Outbox an Subscribers via LISTEN/NOTIFY weiter.

    Holt unverarbeitete Events mit SELECT...FOR UPDATE SKIP LOCKED
    (Schreibsperre zur Verhinderung doppelter Verarbeitung), markiert sie als verarbeitet
    und benachrichtigt Subscribers auf OUTBOX_NOTIFY_CHANNEL.

    Implementiert idempotente Retry-Logik: Events mit retry_count >= max_retries
    werden als verarbeitet markiert, aber für manuelle Überprüfung geloggt.

    Args:
        session: Async SQLAlchemy-Session (muss zu Postgres verbunden sein).
        worker_id: Eindeutige Kennung für diese Worker-Instanz (UUID); wenn None, wird eine neue UUID generiert.
        config: Relay-Konfiguration; nutzt Standardwerte wenn None.

    Raises:
        RuntimeError: Falls die Datenbank nicht Postgres ist oder Verbindung fehlschlägt.
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
                # Keine Events zu verarbeiten; Warten vor nächster Prüfung
                await asyncio.sleep(config.poll_interval_ms / 1000.0)
    except asyncio.CancelledError:
        logger.info(f"Relay worker {worker_id} cancelled")
        raise


async def _relay_batch(
    session: AsyncSession,
    worker_id: UUID,
    config: RelayConfig,
) -> int:
    """Hole und verarbeite einen Batch unverarbeiteter Events.

    Gibt die Anzahl der in diesem Batch verarbeiteten Events zurück.
    """
    try:
        # Prüfe, ob Session verbunden ist
        if session is None:
            raise RuntimeError("Session not connected; cannot relay events")

        # Hole unverarbeitete Events mit Schreibsperre (SKIP LOCKED verhindert Blockierung)
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

        # Verarbeite jedes Event
        for event in events:
            await _process_event(session, event, worker_id, config)

        # Committe den Batch
        await session.commit()

        logger.info(f"Relayed {len(events)} events in batch")
        return len(events)

    except Exception:
        logger.exception("Fehler im Relay-Batch")
        await session.rollback()
        raise


async def _process_event(
    session: AsyncSession,
    event: OutboxEvent,
    worker_id: UUID,
    config: RelayConfig,
) -> None:
    """Verarbeite ein einzelnes Event: Markiere als verarbeitet und benachrichtige Subscribers.

    Falls max. Retries überschritten, markiere als verarbeitet (aufgegeben) und logge.
    Hinweis: processed_at wird auch bei Retry-Aufgabe gesetzt (nach max_retries Versuchen).
    Das bedeutet "verarbeitet (erfolgreich oder aufgegeben)", nicht "erfolgreich".
    """
    try:
        if event.retry_count >= config.max_retries:
            logger.warning(
                f"Event {event.id} exceeded max retries ({config.max_retries}); giving up. "
                f"Last error: {event.last_error}"
            )
        else:
            # Versuche, Subscribers zu benachrichtigen
            await _notify_subscribers(session, event)

        # Markiere Event als verarbeitet mit direktem UPDATE (verhindert Race-Conditions)
        # Nutze text("now()") für server-seitigen Zeitstempel
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
        logger.error(f"Fehler bei Event-Verarbeitung {event.id}: {exc}")
        # Aktualisiere Retry-Count und letzten Fehler
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

        # Exponentieller Backoff vor Retry
        backoff_ms = config.backoff_base_ms * (2**event.retry_count)
        logger.info(f"Event {event.id} retry #{event.retry_count}, backoff {backoff_ms}ms")
        await asyncio.sleep(backoff_ms / 1000.0)


async def _notify_subscribers(
    session: AsyncSession,
    event: OutboxEvent,
) -> None:
    """Benachrichtige Subscribers zu einem neuen Event via LISTEN/NOTIFY.

    Versendet die Event-ID und den Typ auf OUTBOX_NOTIFY_CHANNEL.
    """
    # Prüfe Datenbankverbindung mit SELECT 1
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError("No connection available for NOTIFY") from exc

    # Bereite Benachrichtigungspayload vor als sicheres JSON
    # Nutze json.dumps() statt String-Interpolation, um SQL-Injection zu verhindern
    payload_json = json.dumps(
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
        }
    )

    # NOTIFY mit Escaping (Payload muss mit einfachen Anführungszeichen escaped werden)
    # Escape durch Verdopplung (SQL-Standard)
    escaped_payload = payload_json.replace("'", "''")
    notify_sql = f"NOTIFY {OUTBOX_NOTIFY_CHANNEL}, '{escaped_payload}'"
    await session.execute(text(notify_sql))

    logger.debug(f"Benachrichtigt {OUTBOX_NOTIFY_CHANNEL} für Event {event.id}")
