"""Erfuellt die Naht `RegisterUserEventLog` ueber die Outbox."""

from collections.abc import Mapping
from typing import final

from src.contexts.shared_kernel.events import JsonValue
from src.contexts.shared_kernel.timestamp import Timestamp
from src.infrastructure.outbox.outbox import OutboxTransaction, write_event

__all__ = ["RegisterUserOutbox"]


@final
class RegisterUserOutbox:
    """Schreibt die Ereignisse des Use Case RegisterUser in die Outbox.

    Nimmt die Transaktion des laufenden Vorgangs entgegen, nicht eine eigene -
    siehe `OutboxTransaction` fuer die Begruendung.
    """

    def __init__(self, transaction: OutboxTransaction) -> None:
        """Nimm die laufende Transaktion des Vorgangs entgegen."""
        self._transaction = transaction

    async def record(
        self,
        event_type: str,
        payload: Mapping[str, JsonValue],
        occurred_at: int,
    ) -> None:
        """Lege das Ereignis in die Outbox."""
        await write_event(self._transaction, event_type, payload, Timestamp(occurred_at))
