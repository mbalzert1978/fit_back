"""Die public Naht des Use Case RegisterUser.

Drei Eigenschaften machen das zur Naht *dieses* Use Case und nicht zu einem
geteilten Identity-Gateway (.rules/python/python-feature-slices.md):

1. Nur die Operationen, die `register_user` wirklich braucht - kein `save`,
   kein `delete`, kein `find_by_id`, die andere Use Cases spaeter brauchen.
2. Ueber die Naht wandern ausschliesslich Primitive. Kein Value Object, keine
   Entitaet, kein Aggregat; die Uebersetzung ist Sache der Port-Adapter.
3. Jede fallible Operation liefert ihre **eigene**, einfache Tagged Union -
   nicht `Result[T, DomainError]`. Der Fehlerkanal der Domaene bleibt drinnen.

Wer diese Naht implementiert, ist der Naht egal: in Stufe 1 ein In-Memory-Fake,
in Stufe 2 ein SQLAlchemy-Repository und ein Argon2id-Hasher.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, final

__all__ = [
    "EmailFree",
    "EmailLookup",
    "EmailTaken",
    "NewUserRecord",
    "RegisterUserPasswordHasher",
    "RegisterUserUserStore",
    "UserInsertion",
    "UserStored",
    "WriteCollision",
]


@final
@dataclass(frozen=True, slots=True)
class EmailTaken:
    """Zur angefragten E-Mail existiert bereits ein Konto."""

    user_id: str


@final
@dataclass(frozen=True, slots=True)
class EmailFree:
    """Zur angefragten E-Mail existiert kein Konto."""


type EmailLookup = EmailTaken | EmailFree


@final
@dataclass(frozen=True, slots=True)
class NewUserRecord:
    """Der zu schreibende Datensatz - flach und primitiv, kein Aggregat."""

    user_id: str
    email: str
    password_hash: str = field(repr=False)
    display_name: str
    locale: str
    time_zone_id: str
    status: str
    registered_at: datetime


@final
@dataclass(frozen=True, slots=True)
class UserStored:
    """Der Datensatz wurde geschrieben."""


@final
@dataclass(frozen=True, slots=True)
class WriteCollision:
    """Die E-Mail wurde zwischen Pruefung und Schreiben von einem anderen Vorgang belegt."""

    user_id: str


type UserInsertion = UserStored | WriteCollision


class RegisterUserUserStore(Protocol):
    """Naht zum Nutzerbestand - genau die zwei Operationen dieses Use Case."""

    async def find_by_email(self, normalized_email: str) -> EmailLookup:
        """Suche ein Konto zur bereits normalisierten E-Mail."""
        ...

    async def insert(self, record: NewUserRecord) -> UserInsertion:
        """Schreibe den neuen Datensatz; melde eine Kollision auf der E-Mail."""
        ...


class RegisterUserPasswordHasher(Protocol):
    """Naht zum Hash-Verfahren - nicht fallibel, also ohne Ergebnis-Union."""

    async def hash_password(self, plain_password: str) -> str:
        """Hashe das Klartext-Passwort und liefere den fertigen Hash-String."""
        ...
