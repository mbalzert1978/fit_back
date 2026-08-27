"""Value Object UserId - die validierte Identitaet der Aggregatwurzel User."""

from dataclasses import dataclass, field
from typing import Final, Self, final
from uuid import UUID, uuid7

from src.contexts.identity.domain.user_id_errors import UserIdError, UserIdMalformed
from src.contexts.shared_kernel import ConstructionKey, Err, Ok, Result, deny_foreign_key
from src.contexts.shared_kernel.validation import ParseRule

__all__ = ["UserId"]


def is_well_formed_uuid(candidate: str) -> Result[UUID, UserIdError]:
    """Der Rohwert ist eine wohlgeformte UUID - und kommt als solche zurueck.

    Das `try` ist keine Ausnahme von "nur an der IO-Naht fangen": `ValueError`
    ist hier der Rueckgabekanal von `UUID`, und er endet an dieser Zeile.
    """
    try:
        return Ok(UUID(candidate))
    except ValueError:
        return Err(UserIdMalformed(candidate))


_RULE: ParseRule[str, UUID, UserIdError] = is_well_formed_uuid

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur die drei Factories unten haben ihn."""


@final
@dataclass(frozen=True, slots=True)
class UserId:
    """Identitaet eines Users als zeitsortierte UUIDv7.

    Wird ausschliesslich ueber `generate`, `parse` oder `hydrate` erzeugt - der
    rohe Konstruktor weist jeden anderen Weg ab.
    """

    value: UUID
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch eine der drei Factories ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def generate(cls) -> UserId:
        """Erzeuge eine neue, zeitsortierte Identitaet (UUIDv7)."""
        return cls(uuid7(), key=_KEY)

    @classmethod
    def parse(cls, raw: str) -> Result[Self, UserIdError]:
        """Lies eine Identitaet aus einem moeglicherweise ungueltigen Rohwert."""
        return _RULE(raw).map(lambda checked: cls(checked, key=_KEY))

    @classmethod
    def hydrate(cls, raw: str) -> UserId:
        """Rekonstruiere eine Identitaet aus einer vertrauenswuerdigen Quelle."""
        match cls.parse(raw):
            case Ok(value=user_id):
                return user_id
            case Err():
                msg = f"unreachable: {raw!r} stammt aus vertrauenswuerdiger Quelle"
                raise AssertionError(msg)

    def __str__(self) -> str:
        """Serialisiere die Identitaet fuer Naht und Transport."""
        return str(self.value)
