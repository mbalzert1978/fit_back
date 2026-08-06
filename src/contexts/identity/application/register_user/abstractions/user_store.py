"""Naht zum Nutzerbestand - genau eine Operation, weil es genau eine gibt."""

from dataclasses import dataclass, field
from typing import Protocol, final

__all__ = [
    "EmailTaken",
    "NewUserRecord",
    "RegisterUserUserStore",
    "UserInsertion",
    "UserStored",
]


@final
@dataclass(frozen=True, slots=True)
class NewUserRecord:
    """Der zu schreibende Datensatz - flach und primitiv, kein Aggregat.

    `registered_at` sind Unix-Sekunden (siehe `shared_kernel.Timestamp`), damit
    die Naht in jeder Engine gleich aussieht.
    """

    user_id: str
    email: str
    password_hash: str = field(repr=False)
    display_name: str
    locale: str
    time_zone_id: str
    status: str
    registered_at: int


@final
@dataclass(frozen=True, slots=True)
class UserStored:
    """Der Datensatz wurde geschrieben."""


@final
@dataclass(frozen=True, slots=True)
class EmailTaken:
    """Die E-Mail gehoert bereits einem Konto - der Bestand hat abgelehnt.

    Ohne Angabe, wem: der Ausgang wird nach aussen zu "diese Adresse ist
    vergeben", nie zu "sie gehoert diesem Konto". Damit kommt der Bestand mit
    einem einzigen Statement aus (`ON CONFLICT DO NOTHING RETURNING`) statt mit
    einem Konflikt plus Nachschlage-Abfrage.
    """


type UserInsertion = UserStored | EmailTaken


class RegisterUserUserStore(Protocol):
    """Naht zum Nutzerbestand.

    Bewusst **ohne** vorgelagerte `find_by_email`-Auskunft: eine getrennte
    Pruefung waere im Moment ihrer Beantwortung schon veraltet, und ein
    zusaetzlicher Schritt macht das Wettrennen erst auf, das er verhindern soll.
    Der Bestand entscheidet die Eindeutigkeit beim Schreiben und meldet sie hier.
    """

    async def insert(self, record: NewUserRecord) -> UserInsertion:
        """Schreibe den neuen Datensatz; melde eine bereits vergebene E-Mail."""
        ...
