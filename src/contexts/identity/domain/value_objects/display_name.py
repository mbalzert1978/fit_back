"""Value Object DisplayName - der Anzeigename des Users, 1-60 Zeichen."""

from dataclasses import dataclass
from typing import final

from src.contexts.shared_kernel import Err, NotEmptyString, Ok, Result

__all__ = ["MAXIMUM_LENGTH", "DisplayName"]

MAXIMUM_LENGTH = 60
"""BACKEND.md Abschnitt 1: 1-60 Zeichen. Die untere Grenze traegt `NotEmptyString`."""


def fits_maximum_length(name: NotEmptyString) -> Result[NotEmptyString, str]:
    """Fail-fast-Regel: der Anzeigename ist nicht laenger als erlaubt.

    Nimmt bereits einen `NotEmptyString` entgegen und nicht einen rohen `str` -
    "getrimmt und nicht leer" ist an dieser Stelle schon durch den Typ zugesagt
    und wird deshalb nicht ein zweites Mal geprueft.
    """
    if len(name.value) > MAXIMUM_LENGTH:
        return Err(f"Anzeigename darf hoechstens {MAXIMUM_LENGTH} Zeichen lang sein")
    return Ok(name)


@final
@dataclass(frozen=True, slots=True)
class DisplayName:
    """Anzeigename des Users.

    Haelt einen `NotEmptyString` statt eines rohen `str`: die Invariante "nicht
    leer" steht damit genau einmal im Shared Kernel, und jeder Leser sieht dem
    Typ an, dass hier nichts Leeres liegen kann. `DisplayName` fuegt nur seine
    eigene, fachliche Regel hinzu - die Obergrenze.
    """

    value: NotEmptyString

    @property
    def text(self) -> str:
        """Der rohe Text - nur an Aussengrenzen (Naht, Response-DTO)."""
        return self.value.value

    @classmethod
    def parse(cls, raw: str) -> Result[DisplayName, str]:
        """Pruefe eine moeglicherweise ungueltige Eingabe.

        Ein Fluss statt einer Kette: `NotEmptyString.parse` trimmt und sichert
        die untere Grenze, `fits_maximum_length` prueft die obere, `map` wickelt
        das Ergebnis ein. Jede Frage wird genau einmal gestellt.
        """
        return NotEmptyString.parse(raw).bind(fits_maximum_length).map(cls)

    @classmethod
    def hydrate(cls, raw: str) -> DisplayName:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=display_name):
                return display_name
            case Err():
                raise AssertionError(f"unreachable: {raw!r} wurde vorgelagert validiert")
