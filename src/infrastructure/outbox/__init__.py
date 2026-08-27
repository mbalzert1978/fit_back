"""Postgres-gestuetzte Outbox: Mechanismus fuer Integration Events zwischen Contexts.

Die fachlichen Bausteine (`DomainEvent`, `EventPublisher`, `EventRegistry`)
stehen in `src/contexts/shared_kernel/events.py`, nicht hier. Architektur-Begruendung
siehe `docs/decisions/2026-08-06-1120-outbox-mechanismus-statt-naht.md`.
"""

from src.infrastructure.outbox.outbox import (
    OUTBOX_CHANNEL,
    OutboxTransaction,
    write_event,
)
from src.infrastructure.outbox.relay import OutboxRelay, RelayConfig
from src.infrastructure.outbox.worker import OutboxWorker

__all__ = [
    "OUTBOX_CHANNEL",
    "OutboxRelay",
    "OutboxTransaction",
    "OutboxWorker",
    "RelayConfig",
    "write_event",
]
