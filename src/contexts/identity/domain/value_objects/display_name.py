"""Value Object DisplayName - der Anzeigename des Users, 2-60 Zeichen."""

from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain.display_name_errors import (
    DisplayNameError,
    DisplayNameIsEmpty,
    DisplayNameTooLong,
    DisplayNameTooShort,
)
from src.contexts.shared_kernel import Err, NotEmptyString, Ok, Result

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


def is_long_enough(name: NotEmptyString) -> Result[NotEmptyString, DisplayNameError]:
    """Fail-fast-Regel: der Anzeigename erreicht die Mindestlaenge.

    Steht vor `fits_maximum_length`, damit ein Name, der beides verletzen
    koennte, die Grenze meldet, die er tatsaechlich reisst.
    """
    if len(name.value) < MINIMUM_LENGTH:
        return Err(DisplayNameTooShort(len(name.value), MINIMUM_LENGTH))
    return Ok(name)


def fits_maximum_length(name: NotEmptyString) -> Result[NotEmptyString, DisplayNameError]:
    """Fail-fast-Regel: der Anzeigename ist nicht laenger als erlaubt.

    Nimmt bereits einen `NotEmptyString` entgegen und nicht einen rohen `str` -
    "getrimmt und nicht leer" ist an dieser Stelle schon durch den Typ zugesagt
    und wird deshalb nicht ein zweites Mal geprueft.
    """
    if len(name.value) > MAXIMUM_LENGTH:
        return Err(DisplayNameTooLong(len(name.value), MAXIMUM_LENGTH))
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
    def parse(cls, raw: str) -> Result[DisplayName, DisplayNameError]:
        """Pruefe eine moeglicherweise ungueltige Eingabe.

        Ein Fluss statt einer Kette: `NotEmptyString.parse` trimmt und faengt
        den leeren Namen, `is_long_enough` sichert die untere Grenze,
        `fits_maximum_length` die obere, `map` wickelt das Ergebnis ein. Jede
        Frage wird genau einmal gestellt.

        Das `map_err` ist die Uebersetzung an der Grenze: `NotEmptyString` meldet
        den technischen Fall `TextIsEmpty` ohne Feldbezug, nach aussen gehoert der
        fachliche `DisplayNameIsEmpty` mit eigenem Code. Verkettet statt gematcht,
        weil das Ergebnis ein `Result` bleibt und sich nur sein Fehlertyp aendert
        (.rules/python/python-error-handling.md, "Verketten oder matchen").
        """
        return (
            NotEmptyString.parse(raw)
            .map_err(lambda _: DisplayNameIsEmpty())
            .bind(is_long_enough)
            .bind(fits_maximum_length)
            .map(cls)
        )

    @classmethod
    def hydrate(cls, raw: str) -> DisplayName:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=display_name):
                return display_name
            case Err():
                msg = f"unreachable: {raw!r} wurde vorgelagert validiert"
                raise AssertionError(msg)
