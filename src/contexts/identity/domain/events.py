"""Ereignisse, die der Identity-Context nach aussen meldet."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain.value_objects.locale import Locale, locale_tag
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.shared_kernel.events import JsonValue
from src.shared_kernel.timestamp import Timestamp

__all__ = ["UserRegistered"]


@final
@dataclass(frozen=True, slots=True)
class UserRegistered:
    """Ein Konto ist entstanden.

    Traegt bewusst **nur**, was ein fremder Context zum Reagieren braucht.
    E-Mail und Anzeigename bleiben drinnen: Goals legt ein Default-Profil an,
    Diary seine Standard-Mahlzeiten-Slots - beide brauchen dafuer die Identitaet
    und die Sprache, keine personenbezogenen Angaben. Was hier steht, ist
    ausserhalb dieses Context nicht mehr einzufangen.

    Die Sprache ist dabei kein Beiwerk: Diary benennt seine Standard-Slots
    danach, und ein Nachfragen waere ein synchroner Rueckruf in genau den
    Context, der gerade fire-and-forget gemeldet hat.
    """

    user_id: UserId
    locale: Locale
    registered_at: Timestamp

    @property
    def event_type(self) -> str:
        """Der Name, unter dem sich Consumer auf dieses Ereignis eintragen."""
        return "UserRegistered"

    @property
    def occurred_at(self) -> Timestamp:
        """Ein Konto ist genau dann entstanden, als es registriert wurde."""
        return self.registered_at

    def to_payload(self) -> Mapping[str, JsonValue]:
        """Gib die Fassung heraus, die den Context verlaesst - Primitive, sonst nichts."""
        return {
            "user_id": str(self.user_id),
            "locale": locale_tag(self.locale),
            "registered_at": self.registered_at.unix_seconds,
        }
