"""Event-Publisher: Schreibt Events transaktional mit Aggregat-Writes in Outbox."""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared_infrastructure.outbox import OutboxEvent


async def publish_outbox_event(
    session: AsyncSession,
    event_type: str,
    aggregate_id: UUID,
    aggregate_type: str,
    payload: dict[str, Any],
) -> None:
    """Veröffentliche ein Event in der Outbox zur späteren Relay-Verarbeitung.

    Wird transaktional zusammen mit dem Aggregat-Write aufgerufen, der das Event emittiert.
    Der Relay-Worker (relay_outbox_events) holt unverarbeitete Events
    und benachrichtigt Subscribers via LISTEN/NOTIFY.

    Args:
        session: Async SQLAlchemy-Session (wird vom Aufrufer committed).
        event_type: Event-Typ-Name (z.B. 'UserRegistered').
        aggregate_id: UUID des Aggregats, das das Event emittiert hat.
        aggregate_type: Typ des Aggregats (z.B. 'User').
        payload: Event-Daten als Dict (wird zu JSONB serialisiert).

    Raises:
        ValueError: Falls ein erforderlicher Parameter ungültig ist.
    """
    if not event_type or not isinstance(event_type, str):
        raise ValueError("event_type must be a non-empty string")
    if not aggregate_id:
        raise ValueError("aggregate_id must be a valid UUID")
    if not aggregate_type or not isinstance(aggregate_type, str):
        raise ValueError("aggregate_type must be a non-empty string")
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict")

    event = OutboxEvent(
        id=uuid4(),
        event_type=event_type,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        payload=payload,
    )
    session.add(event)
