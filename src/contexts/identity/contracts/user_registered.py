"""Das veroeffentlichte Ereignis `UserRegistered`."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, final

from src.contexts.shared_kernel.events import JsonValue
from src.contexts.shared_kernel.timestamp import Timestamp

__all__ = ["UserRegistered"]


@final
@dataclass(frozen=True, slots=True)
class UserRegistered:
    """Ein Konto ist entstanden.

    Traegt bewusst **nur**, was ein fremder Context zum Reagieren braucht: Goals
    legt ein Default-Profil an, Diary seine Standard-Mahlzeiten-Slots - beide
    brauchen Identitaet und Sprache, keine personenbezogenen Angaben. E-Mail und
    Anzeigename bleiben im Identity-Context; was hier steht, ist ausserhalb nicht
    mehr einzufangen.

    Die Sprache ist dabei kein Beiwerk: Diary benennt seine Standard-Slots
    danach, und ein Nachfragen waere ein synchroner Rueckruf in genau den
    Context, der gerade fire-and-forget gemeldet hat.

    Primitive statt Value Objects, weil das hier die Aussenseite ist - ein
    `UserId` des Identity-Context haette in Goals nichts verloren.
    """

    EVENT_TYPE: ClassVar[str] = "UserRegistered"
    """Der Name auf der Leitung.

    Als Konstante und nicht als `__name__`: unter diesem Namen liegen bereits
    geschriebene Zeilen in der Outbox, und ein Klassen-Rename waere sonst still
    ein Bruch der Vertraege - genau die Kopplung, die eine Registrierung ueber
    den Typ vermeiden soll.
    """

    user_id: str
    locale: str
    occurred_at: Timestamp

    def to_payload(self) -> Mapping[str, JsonValue]:
        """Gib die Nutzlast heraus - ohne `occurred_at`, das eine eigene Spalte hat."""
        return {"user_id": self.user_id, "locale": self.locale}
