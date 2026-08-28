"""In-Memory-Ereignisprotokoll hinter der public Naht des Use Case RegisterUser."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final

from src.contexts.shared_kernel.events import JsonValue

__all__ = ["InMemoryEventLog", "RecordedEvent"]


@final
@dataclass(frozen=True, slots=True)
class RecordedEvent:
    """Ein festgehaltenes Ereignis, so wie es die Naht passiert hat."""

    event_type: str
    payload: Mapping[str, JsonValue]
    occurred_at: int


@final
class InMemoryEventLog:
    """Erfuellt `RegisterUserEventLog` fuer Specs.

    Bildet nach, was in Stufe 2 die Outbox-Tabelle tut - allerdings nur ihren
    beobachtbaren Teil: dass ein Ereignis festgehalten wurde. Ob es transaktional
    am Nutzer-Datensatz haengt, kann kein In-Memory-Fake zeigen; das entscheidet
    Postgres und wird dort geprueft (tests/infrastructure/test_outbox.py).
    """

    def __init__(self) -> None:
        """Starte ohne festgehaltene Ereignisse."""
        self._recorded: list[RecordedEvent] = []

    @property
    def recorded(self) -> Sequence[RecordedEvent]:
        """Die Ereignisse in der Reihenfolge, in der sie festgehalten wurden."""
        return tuple(self._recorded)

    async def record(
        self,
        event_type: str,
        payload: Mapping[str, JsonValue],
        occurred_at: int,
    ) -> None:
        """Halte das Ereignis fest."""
        self._recorded.append(RecordedEvent(event_type, payload, occurred_at))
