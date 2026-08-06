"""In-Memory-Nutzerbestand hinter der public Naht des Use Case RegisterUser."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    EmailTaken,
    NewUserRecord,
    UserInsertion,
    UserStored,
)

__all__ = ["InMemoryUserStore"]


@final
class InMemoryUserStore:
    """Erfuellt `RegisterUserUserStore` fuer Specs.

    Bildet nach, was in Stufe 2 der Unique-Index auf `identity.users.email` tut:
    die Eindeutigkeit entscheidet sich beim Schreiben, nicht vorher.
    """

    def __init__(self) -> None:
        """Starte mit leerem Bestand."""
        self._taken: set[str] = set()

    def register(self, normalized_email: str) -> None:
        """Lege ein bereits bestehendes Konto an."""
        self._taken.add(normalized_email)

    async def insert(self, record: NewUserRecord) -> UserInsertion:
        """Schreibe den Datensatz oder melde die bereits vergebene E-Mail."""
        if record.email in self._taken:
            return EmailTaken()
        self._taken.add(record.email)
        return UserStored()
