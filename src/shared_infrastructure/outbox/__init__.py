"""Postgres-gestuetzte Outbox: Mechanismus fuer Integration Events zwischen Contexts.

Was hier liegt, ist Transport - kein Slice erfuellt eine Naht dieses Pakets.
Die fachlichen Bausteine (`DomainEvent`, `EventPublisher`, `EventRegistry`)
stehen in `src/shared_kernel/events.py`; ein Slice spricht ausschliesslich mit
denen. Eine duenne Klasse je Slice erfuellt dessen eigene Naht und ruft dafuer
`write_event` auf.
"""

from src.shared_infrastructure.outbox.outbox import (
    OUTBOX_CHANNEL,
    OutboxTransaction,
    write_event,
)
from src.shared_infrastructure.outbox.relay import OutboxRelay, RelayConfig
from src.shared_infrastructure.outbox.worker import OutboxWorker

__all__ = [
    "OUTBOX_CHANNEL",
    "OutboxRelay",
    "OutboxTransaction",
    "OutboxWorker",
    "RelayConfig",
    "write_event",
]
