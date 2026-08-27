"""Integration Events: die beiden Richtungen, in denen Contexts sich erreichen.

Ueber Bande und nicht per direktem Aufruf, damit die Contexts sich spaeter als eigene
Dienste herausloesen lassen (siehe `docs/architecture.md`, Cross-Context-Kommunikation).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import ClassVar, Protocol, final
from uuid import UUID

from src.contexts.shared_kernel.timestamp import Timestamp

__all__ = [
    "DeliveredEvent",
    "DomainEvent",
    "EventHandler",
    "EventPublisher",
    "EventRegistry",
    "JsonValue",
]

type JsonValue = str | int | float | bool | list["JsonValue"] | Mapping[str, "JsonValue"] | None


class DomainEvent(Protocol):
    """Der veroeffentlichte Teil eines Ereignisses - was Fremde importieren duerfen."""

    EVENT_TYPE: ClassVar[str]
    """Der Name auf der Leitung - die einzige Stelle, an der er als String steht."""

    @property
    def occurred_at(self) -> Timestamp:
        """Wann das Ereignis fachlich eingetreten ist.

        Als Property und nicht als Attribut: eingefrorene Vertraege wie `UserRegistered`
        geben die Zusage, dass man den Zeitpunkt ueberschreiben darf, nicht ab.
        """
        ...

    def to_payload(self) -> Mapping[str, JsonValue]:
        """Flache, JSON-faehige Nutzlast fuer den Transport."""
        ...


class EventPublisher(Protocol):
    """Domain-Port: nimmt ein Ereignis entgegen, damit andere Contexts es sehen.

    Ohne `Result`: Ereignis und Aggregate-Write teilen sich eine Transaktion, ein
    fachlicher Ausgang "gespeichert, Ereignis abgelehnt" existiert nicht.
    """

    async def publish(self, event: DomainEvent) -> None:
        """Veroeffentliche das Ereignis."""
        ...


@final
@dataclass(frozen=True, slots=True)
class DeliveredEvent:
    """Ein Ereignis, wie es beim reagierenden Context ankommt - nur Primitive."""

    event_id: UUID
    """Stabile Identitaet der Zustellung - der Schluessel gegen Doppelzustellungen."""

    event_type: str
    payload: Mapping[str, JsonValue]
    occurred_at: Timestamp

    attempt: int
    """Der wievielte Zustellversuch dies ist, beginnend bei 1."""


class EventHandler(Protocol):
    """Die Reaktion eines Contexts auf einen Event-Typ.

    Zustellung ist at-least-once: dieselbe `event_id` kann erneut ankommen, die
    Implementierung muss das aushalten.
    """

    async def handle(self, event: DeliveredEvent, /) -> None:
        """Reagiere auf das Ereignis, oder wirf fuer einen erneuten Versuch."""
        ...


@final
class EventRegistry:
    """Wer auf welchen Event-Typ reagiert.

    Eine Instanz und kein Modul-Global: die Registrierungen gehoeren zur Verdrahtung
    einer Anwendung, nicht zum Importzustand des Prozesses.
    """

    def __init__(self) -> None:
        """Beginne ohne jede Registrierung."""
        self._handlers: dict[str, list[EventHandler]] = {}

    def register[T: DomainEvent](self, event: type[T], handler: EventHandler) -> None:
        """Trage eine Reaktion auf ein Ereignis ein - ueber dessen Typ, nicht seinen Namen."""
        self._handlers.setdefault(event.EVENT_TYPE, []).append(handler)

    def handlers_for(self, event_type: str) -> Sequence[EventHandler]:
        """Liefere die eingetragenen Reaktionen; leer, wenn keine registriert ist."""
        return tuple(self._handlers.get(event_type, ()))
