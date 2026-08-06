"""Value Object NotEmptyString - ein Text, von dem der Typ selbst sagt, dass er da ist.

Ein Feld-Value-Object wie `DisplayName` wrappt dieses hier, statt die
"nicht leer"-Pruefung erneut zu formulieren: die Invariante steht einmal, und
jeder Typ, der ein `NotEmptyString` haelt, weiss ohne Nachfrage, dass sein Text
nicht leer ist.
"""

from dataclasses import dataclass
from typing import final

from src.shared_kernel.result import Err, Ok, Result

__all__ = ["NotEmptyString", "not_blank"]


def not_blank(raw: str) -> Result[str, str]:
    """Fail-fast-Regel: der Text besteht nicht nur aus Leerraum.

    Als eigenstaendige Regel exportiert, damit sie in einer `chain(...)` vor
    laengeren Pruefungen stehen kann, statt in jedem VO neu geschrieben zu werden.
    """
    if not raw.strip():
        return Err("Text darf nicht leer sein")
    return Ok(raw)


@final
@dataclass(frozen=True, slots=True)
class NotEmptyString:
    """Ein garantiert nicht-leerer, getrimmter Text."""

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[NotEmptyString, str]:
        """Trimme und pruefe eine moeglicherweise leere Eingabe."""
        return not_blank(raw).map(lambda text: cls(text.strip()))

    @classmethod
    def hydrate(cls, raw: str) -> NotEmptyString:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=text):
                return text
            case Err():
                raise AssertionError("unreachable: Text wurde vorgelagert validiert")
