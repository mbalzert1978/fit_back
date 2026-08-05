"""Result[T, E] — Basistyp für Operationen mit Erfolgs- oder Fehlschlag-Ausgang."""

from dataclasses import dataclass
from typing import Callable, final


@final
@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Erfolgreicher Ausgang mit Wert."""

    value: T

    def map[U](self, f: Callable[[T], U]) -> "Result[U, E]":
        """Transformiere den erfolgreichen Wert via Funktion."""
        return Ok(f(self.value))

    def bind[U, E](self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Verkette eine Funktion, die selbst Result[U, E] zurückgibt."""
        return f(self.value)


@final
@dataclass(frozen=True, slots=True)
class Err[E]:
    """Fehlschlag-Ausgang mit Fehler."""

    error: E

    def map[T, U](self, f: Callable[[T], U]) -> "Err[E]":
        """Ignoriere den Fehler (Transformation auf Erfolgs-Wert nicht möglich)."""
        return self

    def bind[T, U](self, f: Callable[[T], "Result[U, E]"]) -> "Err[E]":
        """Ignoriere den Fehler (Verkettung nicht möglich)."""
        return self


type Result[T, E] = Ok[T] | Err[E]
