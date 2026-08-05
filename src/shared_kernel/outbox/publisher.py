"""Event publisher: writes events to outbox transactionally with aggregate writes."""

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
    """Publish an event to the outbox for later relay.

    Called transactionally alongside the aggregate write that emitted the event.
    The relay worker (relay_outbox_events) will pick up unprocessed events
    and notify subscribers via LISTEN/NOTIFY.

    Args:
        session: Async SQLAlchemy session (will be committed by the caller).
        event_type: Event type name (e.g., 'UserRegistered').
        aggregate_id: UUID of the aggregate that emitted the event.
        aggregate_type: Type of aggregate (e.g., 'User').
        payload: Event data as a dict (will be serialized to JSONB).

    Raises:
        ValueError: If any required parameter is invalid.
    """
    if not event_type or not isinstance(event_type, str):
        raise ValueError("event_type must be a non-empty string")
    if not aggregate_id:
        raise ValueError("aggregate_id must be a valid UUID")
    if not aggregate_type or not isinstance(aggregate_type, str):
        raise ValueError("aggregate_type must be a non-empty string")
    if not isinstance(payload, dict):
        msg = "payload must be a dict"
        raise TypeError(msg)

    event = OutboxEvent(
        id=uuid4(),
        event_type=event_type,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        payload=payload,
    )
    session.add(event)
