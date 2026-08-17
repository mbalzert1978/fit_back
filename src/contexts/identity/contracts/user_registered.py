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

    Traegt, was die Konsumenten zum Reagieren brauchen: Goals legt ein
    Default-Zielprofil an, Diary seine Standard-Mahlzeiten-Slots. Beide brauchen
    die Identitaet; die Sprache ist dabei kein Beiwerk, weil Diary seine
    Standard-Slots danach benennt, und die Zeitzone entscheidet, welcher
    Kalendertag ein Zeitpunkt fuer diesen Nutzer ist - ohne sie kann Diary keinen
    Tag bilden. Ein Nachfragen waere jedes Mal ein synchroner Rueckruf in genau
    den Context, der gerade fire-and-forget gemeldet hat.

    Der **verbindliche** Feldbestand steht nicht hier, sondern in
    `contracts/events/user_registered/examples/` - eine `.json`-Datei je Fall.
    Bei einer Abweichung ist die Beispiel-Datei massgeblich und dieser Code
    falsch, nicht umgekehrt: sie ist der veroeffentlichte Vertrag, und
    `specs/contracts/test_user_registered_contract.py` misst ihn gegen das
    tatsaechlich emittierte Ereignis. Ein Feld darf additiv dazukommen (neue
    Datei mit erhoehter `<version>`); Umbenennen oder Entfernen ist ein Bruch
    und braucht ein eigenes Ticket, das die Konsumenten mitzieht.

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
    email: str
    locale: str
    time_zone_id: str
    occurred_at: Timestamp
    """Der Zeitpunkt der Registrierung - in der Nutzlast heisst er `registeredAt`."""

    def to_payload(self) -> Mapping[str, JsonValue]:
        """Gib die Nutzlast heraus - camelCase, wie jedes veroeffentlichte JSON dieses Repos.

        `registeredAt` steht **auch** in der Nutzlast, obwohl der Transport den
        Zeitpunkt als eigene Spalte fuehrt: die Nutzlast ist der Vertrag und soll
        fuer sich lesbar sein, ohne dass ein Konsument in den Umschlag greifen
        muss. Als Unix-Sekunden und nicht als ISO-8601 - so haelt es dieses Repo
        ueberall ausser am HTTP-Rand
        (docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md).
        """
        return {
            "userId": self.user_id,
            "email": self.email,
            "locale": self.locale,
            "timeZoneId": self.time_zone_id,
            "registeredAt": self.occurred_at.unix_seconds,
        }
