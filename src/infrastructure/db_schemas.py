"""ORM-Modelle (SQLAlchemy) für kontextübergreifend geteilte Tabellen.

Eigenes Top-Level-Paket, damit `shared_kernel` frei von SQLAlchemy bleibt.
"""

from datetime import datetime
from typing import ClassVar, final
from uuid import UUID

from sqlalchemy import BigInteger, Column, DateTime, SmallInteger, String, Text, Uuid
from sqlalchemy.orm import declarative_base

Base = declarative_base()


@final
class IdempotencyKey(Base):
    """ORM-Modell für die Nachverfolgung von Idempotency-Keys.

    TTL: 7 Tage (Aufräumen per geplantem Job, Ticket 0046).
    """

    __tablename__ = "idempotency_keys"
    __table_args__: ClassVar = {"schema": "shared_kernel"}

    id: Column[int] = Column(BigInteger, primary_key=True, autoincrement=True)

    key: Column[UUID] = Column(Uuid, nullable=False, unique=True)

    user_id: Column[UUID] = Column(Uuid, nullable=False, index=False)
    """FK auf identity.users.id."""

    request_hash: Column[str] = Column(String(64), nullable=False)
    """SHA-256-Hash aus (Methode + Pfad + Body) als Hex-String."""

    response_body: Column[str] = Column(Text, nullable=True)
    """NULL = reserviert, Antwort steht noch aus."""

    response_status: Column[int] = Column(SmallInteger, nullable=True)
    """NULL = vor `shared_005` erfasst."""

    response_headers: Column[str] = Column(Text, nullable=True)
    """JSON-Objekt; NULL = vor `shared_005` erfasst."""

    created_utc: Column[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    def __repr__(self) -> str:
        """Liefert eine String-Repräsentation für das Debugging."""
        return (
            f"<IdempotencyKey(key={self.key!r}, user_id={self.user_id!r}, "
            f"created_utc={self.created_utc!r})>"
        )
