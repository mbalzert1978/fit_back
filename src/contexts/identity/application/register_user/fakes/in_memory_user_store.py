"""In-Memory-Nutzerbestand hinter der public Naht des Use Case RegisterUser."""

from typing import final

from src.contexts.identity.application.register_user.gateway import (
    EmailFree,
    EmailLookup,
    EmailTaken,
    NewUserRecord,
    UserInsertion,
    UserStored,
    WriteCollision,
)

__all__ = ["InMemoryUserStore"]


@final
class InMemoryUserStore:
    """Erfuellt `RegisterUserUserStore` fuer Specs.

    Kennt zwei Arten von Vorbelegung, weil die Naht zwei Fehlschlaege kennt:
    ein bereits sichtbares Konto (`register`) und ein Konto, das erst zwischen
    Pruefung und Schreiben entsteht (`arm_write_collision`) - das Wettrennen,
    das in Stufe 2 der Unique-Index abfaengt.
    """

    def __init__(self) -> None:
        """Starte mit leerem Bestand und ohne vorbereitetes Wettrennen."""
        self._by_email: dict[str, str] = {}
        self._collisions: dict[str, str] = {}

    def register(self, normalized_email: str, user_id: str) -> None:
        """Lege ein bereits bestehendes, sichtbares Konto an."""
        self._by_email[normalized_email] = user_id

    def arm_write_collision(self, normalized_email: str, user_id: str) -> None:
        """Belege die E-Mail erst beim Schreiben, nicht schon bei der Pruefung."""
        self._collisions[normalized_email] = user_id

    async def find_by_email(self, normalized_email: str) -> EmailLookup:
        """Suche ein sichtbares Konto zur bereits normalisierten E-Mail."""
        if (user_id := self._by_email.get(normalized_email)) is None:
            return EmailFree()
        return EmailTaken(user_id)

    async def insert(self, record: NewUserRecord) -> UserInsertion:
        """Schreibe den Datensatz oder melde die Kollision auf der E-Mail."""
        if (user_id := self._collisions.pop(record.email, None)) is not None:
            self._by_email[record.email] = user_id
            return WriteCollision(user_id)
        if (owner := self._by_email.get(record.email)) is not None:
            return WriteCollision(owner)
        self._by_email[record.email] = record.user_id
        return UserStored()
