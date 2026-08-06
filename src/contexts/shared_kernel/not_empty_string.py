"""Value Object NotEmptyString - ein Text, von dem der Typ selbst sagt, dass er da ist.

Ein Feld-Value-Object wie `DisplayName` wrappt dieses hier, statt die
"nicht leer"-Pruefung erneut zu formulieren: die Invariante steht einmal, und
jeder Typ, der ein `NotEmptyString` haelt, weiss ohne Nachfrage, dass sein Text
nicht leer ist.
"""

from dataclasses import dataclass
from typing import final

from src.contexts.shared_kernel.result import Err, Ok, Result

__all__ = ["NotEmptyString", "not_blank"]


def not_blank(raw: str) -> Result[str, str]:
    """Fail-fast-Regel: der Text besteht nicht nur aus Leerraum - und kommt getrimmt zurueck.

    Als eigenstaendige Regel exportiert, damit sie in einer `chain(...)` vor
    laengeren Pruefungen stehen kann, statt in jedem VO neu geschrieben zu werden.

    Das Ergebnis ist der **getrimmte** Text: die Regel muss ohnehin trimmen, um
    ueberhaupt urteilen zu koennen, und jeder Aufrufer will danach dasselbe. Gaebe
    sie den Rohwert zurueck, muesste jede nachgelagerte Pruefung erneut trimmen -
    und wer es vergisst, laesst Leerraum in ein Value Object.
    """
    trimmed = raw.strip()
    if not trimmed:
        return Err("Text darf nicht leer sein")
    return Ok(trimmed)


@final
@dataclass(frozen=True, slots=True)
class NotEmptyString:
    """Ein garantiert nicht-leerer, getrimmter Text."""

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[NotEmptyString, str]:
        """Trimme und pruefe eine moeglicherweise leere Eingabe."""
        return not_blank(raw).map(cls)

    @classmethod
    def hydrate(cls, raw: str) -> NotEmptyString:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=text):
                return text
            case Err():
                raise AssertionError("unreachable: Text wurde vorgelagert validiert")
