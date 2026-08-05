"""ORM models (SQLAlchemy) for cross-context shared tables.

Separate top-level package from `shared_kernel`, not a subfolder of it:
`shared_kernel` (Result[T,E], TimeProvider, ...) must stay free of external
(SQLAlchemy) dependencies, so its infrastructure counterpart lives here
instead of nested underneath it.
"""

from typing import ClassVar, final

from sqlalchemy import BigInteger, Column, DateTime, String, Text, Uuid
from sqlalchemy.orm import declarative_base

# Base for all ORM models
Base = declarative_base()


@final
class IdempotencyKey(Base):
    """ORM model for idempotency key tracking.

    Stores Idempotency-Key headers and their responses for deduplication.
    TTL: 7 days (cleanup via scheduled job, Ticket 0046).
    """

    __tablename__ = "idempotency_keys"
    __table_args__: ClassVar = {"schema": "shared_kernel"}

    id: Column[BigInteger] = Column(BigInteger, primary_key=True, autoincrement=True)
    """Synthetic primary key (BIGSERIAL)."""

    key: Column[Uuid] = Column(Uuid, nullable=False, unique=True)
    """Idempotency-Key value (UUID)."""

    user_id: Column[Uuid] = Column(Uuid, nullable=False, index=False)
    """Owner of the idempotency key (FK to identity.users.id)."""

    request_hash: Column[String] = Column(String(64), nullable=False)
    """SHA-256 hash of (method + path + body) as hex string."""

    response_body: Column[Text] = Column(Text, nullable=False)
    """Cached response body (JSON string)."""

    created_utc: Column[DateTime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    """Creation timestamp in UTC."""

    def __repr__(self) -> str:
        """Provide string representation for debugging."""
        return (
            f"<IdempotencyKey(key={self.key!r}, user_id={self.user_id!r}, "
            f"created_utc={self.created_utc!r})>"
        )
