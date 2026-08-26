"""ORM-Modelle (SQLAlchemy) für kontextübergreifend geteilte Tabellen.

Eigenes Top-Level-Paket, kein Unterordner von `shared_kernel`:
`shared_kernel` (Result[T, E], TimeProvider, ...) muss frei von externen
(SQLAlchemy-)Abhängigkeiten bleiben, deshalb liegt sein Infrastruktur-Gegenstück
hier statt darunter verschachtelt.
"""

from datetime import datetime
from typing import ClassVar, final
from uuid import UUID

from sqlalchemy import BigInteger, Column, DateTime, SmallInteger, String, Text, Uuid
from sqlalchemy.orm import declarative_base

# Basis für alle ORM-Modelle
Base = declarative_base()


@final
class IdempotencyKey(Base):
    """ORM-Modell für die Nachverfolgung von Idempotency-Keys.

    Speichert Idempotency-Key-Header und ihre Antworten zur Deduplizierung.
    TTL: 7 Tage (Aufräumen per geplantem Job, Ticket 0046).
    """

    __tablename__ = "idempotency_keys"
    __table_args__: ClassVar = {"schema": "shared_kernel"}

    id: Column[int] = Column(BigInteger, primary_key=True, autoincrement=True)
    """Synthetischer Primärschlüssel (BIGSERIAL)."""

    key: Column[UUID] = Column(Uuid, nullable=False, unique=True)
    """Wert des Idempotency-Key (UUID)."""

    user_id: Column[UUID] = Column(Uuid, nullable=False, index=False)
    """Eigentümer des Idempotency-Key (FK auf identity.users.id)."""

    request_hash: Column[str] = Column(String(64), nullable=False)
    """SHA-256-Hash aus (Methode + Pfad + Body) als Hex-String."""

    response_body: Column[str] = Column(Text, nullable=True)
    """Gecachter Response-Body (JSON-String). NULL = reserviert, Antwort steht noch aus."""

    response_status: Column[int] = Column(SmallInteger, nullable=True)
    """HTTP-Statuscode der gecachten Antwort. NULL = vor `shared_005` erfasst."""

    response_headers: Column[str] = Column(Text, nullable=True)
    """Wiederabspielbare Response-Header als JSON-Objekt. NULL = vor `shared_005` erfasst."""

    created_utc: Column[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    """Erstellungszeitpunkt in UTC."""

    def __repr__(self) -> str:
        """Liefert eine String-Repräsentation für das Debugging."""
        return (
            f"<IdempotencyKey(key={self.key!r}, user_id={self.user_id!r}, "
            f"created_utc={self.created_utc!r})>"
        )
