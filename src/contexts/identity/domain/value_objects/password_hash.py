"""Value Object PasswordHash - das Ergebnis des Hashers, nie ein roher String."""

from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain.password_hash_errors import PasswordHashError, PasswordHashIsEmpty
from src.contexts.shared_kernel import Err, Ok, Result

__all__ = ["PasswordHash"]


@final
@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Undurchsichtiger Hash-Wert inklusive Algorithmus-Praefix (Argon2id).

    Der Domaene ist der Aufbau des Werts egal - sie prueft nur, dass ueberhaupt
    einer da ist. Das Verfahren lebt hinter dem `PasswordHasher`-Port.
    """

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[PasswordHash, PasswordHashError]:
        """Pruefe, dass der Hasher ueberhaupt einen Wert geliefert hat."""
        return Ok(cls(raw)) if raw.strip() else Err(PasswordHashIsEmpty())

    @classmethod
    def hydrate(cls, raw: str) -> PasswordHash:
        """Rekonstruiere aus einer vertrauenswuerdigen Quelle (Hasher, Persistenz)."""
        match cls.parse(raw):
            case Ok(value=password_hash):
                return password_hash
            case Err():
                msg = "unreachable: Hash stammt aus vertrauenswuerdiger Quelle"
                raise AssertionError(msg)
