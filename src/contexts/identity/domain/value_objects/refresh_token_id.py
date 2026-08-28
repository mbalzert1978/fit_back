"""Value Object RefreshTokenId - die Identitaet des Aggregats RefreshToken."""

from dataclasses import dataclass, field
from typing import Final, final
from uuid import UUID, uuid7

from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["RefreshTokenId"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `generate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class RefreshTokenId:
    """Identitaet eines Refresh-Token als zeitsortierte UUIDv7.

    Nur `generate`, kein `parse` und kein `hydrate`: heute entsteht diese Id
    ausschliesslich beim Ausstellen. Gelesen wird ein Refresh-Token erst beim
    Einloesen (#52); der Weg zurueck aus der Datenbank kommt mit dem Aufrufer,
    der ihn braucht, nicht auf Vorrat.
    """

    value: UUID
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `generate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def generate(cls) -> RefreshTokenId:
        """Erzeuge eine neue, zeitsortierte Identitaet (UUIDv7)."""
        return cls(uuid7(), key=_KEY)

    def __str__(self) -> str:
        """Serialisiere die Identitaet fuer Naht und Transport."""
        return str(self.value)
