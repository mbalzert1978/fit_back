"""Value Object Password - das noch ungehashte, laengengeprueft Klartext-Passwort."""

from dataclasses import dataclass, field
from typing import final

from src.contexts.identity.domain.password_errors import (
    PasswordError,
    PasswordTooLong,
    PasswordTooShort,
)
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import ResultRule, chain

__all__ = ["MAXIMUM_LENGTH", "MINIMUM_LENGTH", "Password"]

MINIMUM_LENGTH = 10
"""Mindestlaenge laut BACKEND.md Abschnitt 1 (kuerzer ⇒ errors.password)."""

MAXIMUM_LENGTH = 128
"""Hoechstlaenge laut Vertrag des Frontends (`contracts/pacts/identity/`,
Ticket #95): 129 Zeichen ⇒ 422 mit einem Eintrag unter `errors.password`."""


def meets_minimum_length(candidate: str) -> Result[str, PasswordError]:
    """Fail-fast-Regel zur Mindestlaenge."""
    if len(candidate) < MINIMUM_LENGTH:
        return Err(PasswordTooShort(len(candidate), MINIMUM_LENGTH))
    return Ok(candidate)


def fits_maximum_length(candidate: str) -> Result[str, PasswordError]:
    """Fail-fast-Regel zur Hoechstlaenge."""
    if len(candidate) > MAXIMUM_LENGTH:
        return Err(PasswordTooLong(len(candidate), MAXIMUM_LENGTH))
    return Ok(candidate)


_RULES: ResultRule[str, PasswordError] = chain(meets_minimum_length, fits_maximum_length)


@final
@dataclass(frozen=True, slots=True)
class Password:
    """Klartext-Passwort auf dem kurzen Weg zum Hasher.

    Das Feld ist bewusst `repr=False`: ein Klartext-Passwort darf nie in einem
    Log, einem Traceback oder einer Fehlermeldung auftauchen.
    """

    value: str = field(repr=False)

    @classmethod
    def parse(cls, raw: str) -> Result[Password, PasswordError]:
        """Pruefe eine moeglicherweise ungueltige Eingabe.

        `.map(cls)` erst am Ende - sonst muesste ein ungueltiges `Password`
        gebaut werden, nur um es danach zu pruefen.
        """
        return _RULES(raw).map(cls)

    @classmethod
    def hydrate(cls, raw: str) -> Password:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=password):
                return password
            case Err():
                msg = "unreachable: Passwort wurde vorgelagert validiert"
                raise AssertionError(msg)
