"""Value Object PasswordHash - das Ergebnis des Hashers, nie ein roher String."""

from dataclasses import dataclass
from typing import final

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
    def parse(cls, raw: str) -> Result[PasswordHash, str]:
        """Pruefe, dass der Hasher ueberhaupt einen Wert geliefert hat."""
        if not raw.strip():
            return Err("Passwort-Hash darf nicht leer sein")
        return Ok(cls(raw))

    @classmethod
    def hydrate(cls, raw: str) -> PasswordHash:
        """Rekonstruiere aus einer vertrauenswuerdigen Quelle (Hasher, Persistenz)."""
        match cls.parse(raw):
            case Ok(value=password_hash):
                return password_hash
            case Err():
                raise AssertionError("unreachable: Hash stammt aus vertrauenswuerdiger Quelle")
