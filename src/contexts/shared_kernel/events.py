"""Integration Events: die beiden Richtungen, in denen Contexts sich erreichen.

Beides sind **Domaenenbausteine**, keine Infrastruktur - dieses Modul haengt nur
an der stdlib und am `Result`. Wer Events tatsaechlich transportiert (Postgres-
Outbox, spaeter vielleicht etwas anderes), steht hier nirgends.

- **Hinaus**: ein Handler haelt ein `DomainEvent` fest und uebergibt es dem Port
  `EventPublisher`. Fuer den Handler endet die Reise damit; ob dahinter eine
  Tabelle, ein Broker oder ein Testdouble steht, sieht er nie.
- **Herein**: ein Context traegt in die `EventRegistry` ein, auf welchen
  Event-Typ er reagieren will. Der Zusteller liest diese Registrierungen und
  ruft, was dort steht - er kennt die Consumer also nicht, sondern findet sie.

Warum ueberhaupt ueber Bande und nicht per direktem Aufruf: die Contexts sollen
sich spaeter als eigene Dienste herausloesen lassen, ohne ihre Logik neu zu
schreiben (siehe CLAUDE.md, "Cross-Context-Kommunikation"). Ein direkter
In-Process-Aufruf waere genau die Kopplung, die das verhindert.
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
    """Der veroeffentlichte Teil eines Ereignisses - was Fremde importieren duerfen.

    Wohnt im `contracts/`-Paket seines Context, nicht in dessen Domaene: ein
    Konsument soll auf ein Ereignis reagieren koennen, ohne die Aggregate,
    Value Objects und Fehlertypen des Erzeugers mitzuziehen. Entsprechend traegt
    ein Ereignis Primitive, keine Value Objects des Erzeugers.

    Bewusst ein Protocol und keine Basisklasse: der Context besitzt seinen
    Vertrag, hier steht nur, was ein Transport davon braucht.
    """

    EVENT_TYPE: ClassVar[str]
    """Der Name auf der Leitung - die einzige Stelle, an der er als String steht."""

    occurred_at: Timestamp
    """Wann das Ereignis fachlich eingetreten ist."""

    def to_payload(self) -> Mapping[str, JsonValue]:
        """Flache, JSON-faehige Nutzlast fuer den Transport.

        Der schreibende Context entscheidet hier, was er nach aussen zeigt - das
        ist die Stelle, an der ein Aggregat nicht versehentlich komplett
        veroeffentlicht wird.
        """
        ...


class EventPublisher(Protocol):
    """Domain-Port: nimmt ein Ereignis entgegen, damit andere Contexts es sehen.

    Bewusst **ohne** `Result`: das Ereignis wird in derselben Transaktion
    festgehalten wie der Aggregate-Write, der es ausgeloest hat. Es gibt keinen
    fachlichen Ausgang "Aggregat gespeichert, Ereignis abgelehnt" - entweder
    beides oder keines. Ein Fehlerkanal haette hier nur einen Fall, den niemand
    erreichen kann, und den Aufrufer gezwungen, ihn trotzdem zu behandeln.

    Ein technischer Ausfall der Datenbank ist kein Rueckgabewert; er reisst die
    Transaktion ohnehin ab.
    """

    async def publish(self, event: DomainEvent) -> None:
        """Veroeffentliche das Ereignis."""
        ...


@final
@dataclass(frozen=True, slots=True)
class DeliveredEvent:
    """Ein Ereignis, wie es beim reagierenden Context ankommt - nur Primitive."""

    event_id: UUID
    """Stabile Identitaet der Zustellung. Der Schluessel, ueber den ein Consumer
    Doppelzustellungen erkennt."""

    event_type: str
    payload: Mapping[str, JsonValue]
    occurred_at: Timestamp

    attempt: int
    """Der wievielte Zustellversuch dies ist, beginnend bei 1."""


class EventHandler(Protocol):
    """Die Reaktion eines Contexts auf einen Event-Typ.

    Zustellung ist **at-least-once**: dieselbe `event_id` kann erneut ankommen,
    wenn ein Prozess nach der Reaktion, aber vor dem Commit abbricht. Die
    Implementierung muss das aushalten. Eine Exception bedeutet "nicht
    verarbeitet" und loest einen weiteren Versuch aus.
    """

    async def handle(self, event: DeliveredEvent) -> None:
        """Reagiere auf das Ereignis, oder wirf fuer einen erneuten Versuch."""
        ...


@final
class EventRegistry:
    """Wer auf welchen Event-Typ reagiert.

    Bewusst eine Instanz und kein Modul-Global: die Registrierungen gehoeren zur
    Verdrahtung einer Anwendung, nicht zum Importzustand des Prozesses - ein
    Test baut sich seine eigene Registry, statt eine globale aufzuraeumen.

    Gefuellt wird sie beim Aufbau, von der Pipeline des reagierenden Use Case;
    gelesen wird sie vom Zusteller. Beide Seiten kennen einander dadurch nicht.
    """

    def __init__(self) -> None:
        """Beginne ohne jede Registrierung."""
        self._handlers: dict[str, list[EventHandler]] = {}

    def register[T: DomainEvent](self, event: type[T], handler: EventHandler) -> None:
        """Trage eine Reaktion auf ein Ereignis ein - ueber dessen Typ, nicht ueber seinen Namen.

        `registry.register(UserRegistered, handler)`: der Import macht die
        Abhaengigkeit sichtbar, und ein Vertippen ist ein Fehler beim Aufbau
        statt einer Reaktion, die im Betrieb schlicht nie kommt. Der String
        steht genau einmal, naemlich als `EVENT_TYPE` im Vertrag selbst.

        Mehrere Reaktionen auf dasselbe Ereignis sind der Normalfall, nicht die
        Ausnahme: auf `UserRegistered` legt Goals ein Default-Profil an *und*
        Diary seine Standard-Mahlzeiten-Slots. Die Reihenfolge ist die der
        Registrierung, aber niemand darf sich darauf verlassen - die beiden
        wissen nichts voneinander.
        """
        self._handlers.setdefault(event.EVENT_TYPE, []).append(handler)

    def handlers_for(self, event_type: str) -> Sequence[EventHandler]:
        """Liefere die eingetragenen Reaktionen; leer, wenn keine registriert ist.

        Hier steht der Name als String, weil er hier auch als String ankommt -
        aus einer Outbox-Zeile, geschrieben womoeglich von einer aelteren
        Version. Das ist die Zustellseite, nicht die Registrierungsseite.

        Ein Event ohne Reaktion ist kein Fehler. Ein Context veroeffentlicht,
        was fachlich passiert ist - ob das gerade jemanden interessiert, ist
        nicht seine Frage.
        """
        return tuple(self._handlers.get(event_type, ()))
