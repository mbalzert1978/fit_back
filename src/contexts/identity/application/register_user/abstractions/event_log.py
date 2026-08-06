"""Naht zum Ereignisprotokoll - eine Operation, keine Ergebnis-Union.

Kein Tagged-Union-Ergebnis, weil es keinen fachlichen Fehlausgang gibt: das
Ereignis wird in derselben Transaktion festgehalten wie der Nutzer-Datensatz.
Entweder beides oder keines - siehe `shared_kernel.events.EventPublisher`.
"""

from collections.abc import Mapping
from typing import Protocol

from src.contexts.shared_kernel.events import JsonValue

__all__ = ["RegisterUserEventLog"]


class RegisterUserEventLog(Protocol):
    """Naht zum Ereignisprotokoll dieses Use Case."""

    async def record(
        self,
        event_type: str,
        payload: Mapping[str, JsonValue],
        occurred_at: int,
    ) -> None:
        """Halte ein Ereignis fest; `occurred_at` sind Unix-Sekunden."""
        ...
