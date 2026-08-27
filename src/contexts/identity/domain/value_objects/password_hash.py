"""Value Object PasswordHash - das Ergebnis des Hashers, nie ein roher String."""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.identity.domain.password_hash_errors import PasswordHashError, PasswordHashIsEmpty
from src.contexts.shared_kernel import ConstructionKey, Err, Ok, Result, deny_foreign_key, not_blank

__all__ = ["PasswordHash"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `parse` und `hydrate` unten haben ihn."""


@final
@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Undurchsichtiger Hash-Wert inklusive Algorithmus-Praefix (Argon2id).

    Der Domaene ist der Aufbau des Werts egal - sie prueft nur, dass ueberhaupt
    einer da ist. Das Verfahren lebt hinter dem `PasswordHasher`-Port.
    """

    value: str
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `parse` oder `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def parse(cls, raw: str) -> Result[Self, PasswordHashError]:
        """Pruefe, dass der Hasher ueberhaupt einen Wert geliefert hat."""
        return (
            not_blank(raw)
            .map_err(lambda _: PasswordHashIsEmpty())
            .map(lambda checked: cls(checked, key=_KEY))
        )

    @classmethod
    def hydrate(cls, raw: str) -> PasswordHash:
        """Rekonstruiere aus einer vertrauenswuerdigen Quelle (Hasher, Persistenz)."""
        match cls.parse(raw):
            case Ok(value=password_hash):
                return password_hash
            case Err():
                msg = "unreachable: Hash stammt aus vertrauenswuerdiger Quelle"
                raise AssertionError(msg)
