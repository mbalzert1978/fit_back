"""Value Object DisplayName - der Anzeigename des Users, 2-60 Zeichen."""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.identity.domain.display_name_errors import (
    DisplayNameError,
    DisplayNameIsEmpty,
    DisplayNameTooLong,
    DisplayNameTooShort,
)
from src.contexts.shared_kernel import (
    ConstructionKey,
    Err,
    Ok,
    Result,
    deny_foreign_key,
    not_blank_as,
)
from src.contexts.shared_kernel.validation import ResultRule, chain

__all__ = ["MAXIMUM_LENGTH", "MINIMUM_LENGTH", "DisplayName"]

MINIMUM_LENGTH = 2
"""Zwei Zeichen, nicht eines.

Der Vertrag des Frontends schickt `"a"` und erwartet dafuer einen Eintrag unter
`errors.displayName`
(`docs/decisions/2026-08-21-2200-vertrag-zieht-anzeigename-und-zeitzone-nach.md`).
Wo Vertrag und Invariante kollidieren, gewinnt der Vertrag - `BACKEND.md`
Abschnitt 1 ist entsprechend nachgezogen.
"""

MAXIMUM_LENGTH = 60
"""BACKEND.md Abschnitt 1: 2-60 Zeichen."""


is_not_blank: ResultRule[str, DisplayNameError] = not_blank_as(DisplayNameIsEmpty)
"""Der Anzeigename besteht nicht nur aus Leerraum - und kommt getrimmt zurueck."""


def is_long_enough(candidate: str) -> Result[str, DisplayNameError]:
    """Fail-fast-Regel zur Mindestlaenge - laeuft nach `is_not_blank`."""
    if len(candidate) < MINIMUM_LENGTH:
        return Err(DisplayNameTooShort(len(candidate), MINIMUM_LENGTH))
    return Ok(candidate)


def fits_maximum_length(candidate: str) -> Result[str, DisplayNameError]:
    """Fail-fast-Regel zur Hoechstlaenge."""
    if len(candidate) > MAXIMUM_LENGTH:
        return Err(DisplayNameTooLong(len(candidate), MAXIMUM_LENGTH))
    return Ok(candidate)


_RULES: ResultRule[str, DisplayNameError] = chain(
    is_not_blank,
    is_long_enough,
    fits_maximum_length,
)

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `parse` und `hydrate` unten haben ihn."""


@final
@dataclass(frozen=True, slots=True)
class DisplayName:
    """Anzeigename des Users - getrimmt und laengengeprueft."""

    value: str
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `parse` oder `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def parse(cls, raw: str) -> Result[Self, DisplayNameError]:
        """Pruefe eine moeglicherweise ungueltige Eingabe."""
        return _RULES(raw).map(lambda checked: cls(checked, key=_KEY))

    @classmethod
    def hydrate(cls, raw: str) -> DisplayName:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=display_name):
                return display_name
            case Err():
                msg = f"unreachable: {raw!r} wurde vorgelagert validiert"
                raise AssertionError(msg)
