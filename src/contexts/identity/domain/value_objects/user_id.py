"""Value Object UserId - die validierte Identitaet der Aggregatwurzel User."""

from dataclasses import dataclass
from typing import final
from uuid import UUID, uuid7

from src.contexts.identity.domain.user_id_errors import UserIdError, UserIdMalformed
from src.contexts.shared_kernel import Err, Ok, Result

__all__ = ["UserId"]


@final
@dataclass(frozen=True, slots=True)
class UserId:
    """Identitaet eines Users als zeitsortierte UUIDv7.

    Wird ausschliesslich ueber `generate`, `parse` oder `hydrate` erzeugt - nie
    ueber den rohen Konstruktor ausserhalb dieses Moduls.
    """

    value: UUID

    @classmethod
    def generate(cls) -> UserId:
        """Erzeuge eine neue, zeitsortierte Identitaet (UUIDv7)."""
        return cls(uuid7())

    @classmethod
    def parse(cls, raw: str) -> Result[UserId, UserIdError]:
        """Lies eine Identitaet aus einem moeglicherweise ungueltigen Rohwert."""
        try:
            return Ok(cls(UUID(raw)))
        except ValueError:
            return Err(UserIdMalformed(raw))

    @classmethod
    def hydrate(cls, raw: str) -> UserId:
        """Rekonstruiere eine Identitaet aus einer vertrauenswuerdigen Quelle."""
        match cls.parse(raw):
            case Ok(value=user_id):
                return user_id
            case Err():
                raise AssertionError(f"unreachable: {raw!r} stammt aus vertrauenswuerdiger Quelle")

    def __str__(self) -> str:
        """Serialisiere die Identitaet fuer Naht und Transport."""
        return str(self.value)
