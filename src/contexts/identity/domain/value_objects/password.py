"""Value Object Password - das noch ungehashte, laengengeprueft Klartext-Passwort."""

from dataclasses import dataclass, field
from typing import final

from src.shared_kernel import Err, Ok, Result

__all__ = ["MINIMUM_LENGTH", "Password"]

MINIMUM_LENGTH = 10
"""Mindestlaenge laut BACKEND.md Abschnitt 1 (kuerzer ⇒ errors.password)."""


@final
@dataclass(frozen=True, slots=True)
class Password:
    """Klartext-Passwort auf dem kurzen Weg zum Hasher.

    Das Feld ist bewusst `repr=False`: ein Klartext-Passwort darf nie in einem
    Log, einem Traceback oder einer Fehlermeldung auftauchen.
    """

    value: str = field(repr=False)

    @classmethod
    def parse(cls, raw: str) -> Result[Password, str]:
        """Pruefe die Mindestlaenge einer moeglicherweise ungueltigen Eingabe."""
        if len(raw) < MINIMUM_LENGTH:
            return Err(f"Passwort muss mindestens {MINIMUM_LENGTH} Zeichen lang sein")
        return Ok(cls(raw))

    @classmethod
    def hydrate(cls, raw: str) -> Password:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=password):
                return password
            case Err():
                raise AssertionError("unreachable: Passwort wurde vorgelagert validiert")
