"""SQLAlchemy ORM model for shared.outbox table.

Stores integration events emitted by aggregates, awaiting relay to subscribed contexts.
"""

from typing import ClassVar, final

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import declarative_base

Base = declarative_base()


@final
class OutboxEvent(Base):
    """ORM model for outbox event storage.

    Events are written transactionally with aggregate writes and relayed asynchronously
    via SELECT...FOR UPDATE SKIP LOCKED to prevent duplicate processing.
    """

    __tablename__ = "outbox"
    __table_args__: ClassVar = {"schema": "shared"}

    id: Column[Uuid] = Column(Uuid, nullable=False, primary_key=True)
    """Unique event identifier (UUID)."""

    event_type: Column[String] = Column(String(255), nullable=False)
    """Event type (e.g., 'UserRegistered', 'UserDeleted')."""

    payload: Column[dict] = Column(JSON, nullable=False)
    """Event payload as JSONB."""

    aggregate_id: Column[Uuid] = Column(Uuid, nullable=False)
    """ID of the aggregate that emitted this event."""

    aggregate_type: Column[String] = Column(String(255), nullable=False)
    """Type of the aggregate (e.g., 'User', 'Goal')."""

    created_at: Column[DateTime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    """Timestamp when event was created (UTC)."""

    processed_at: Column[DateTime] = Column(DateTime(timezone=True), nullable=True)
    """Timestamp when event was processed by a relay worker (UTC), NULL if unprocessed."""

    processed_by: Column[Uuid] = Column(Uuid, nullable=True)
    """ID of the relay worker instance that processed this event."""

    retry_count: Column[Integer] = Column(Integer, nullable=False, server_default="0")
    """Number of times relay has been attempted."""

    last_error: Column[Text] = Column(Text, nullable=True)
    """Error message from the most recent relay attempt, if any."""

    def __repr__(self) -> str:
        """Provide string representation for debugging."""
        return (
            f"<OutboxEvent("
            f"id={self.id!r}, event_type={self.event_type!r}, "
            f"aggregate_id={self.aggregate_id!r}, aggregate_type={self.aggregate_type!r}, "
            f"created_at={self.created_at!r}, processed_at={self.processed_at!r}"
            f")>"
        )
