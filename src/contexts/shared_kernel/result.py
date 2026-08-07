"""Result[T, E] — Basistyp für Operationen mit Erfolgs- oder Fehlschlag-Ausgang."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import final


@final
@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Erfolgreicher Ausgang mit Wert."""

    value: T

    def map[U](self, f: Callable[[T], U]) -> Ok[U]:
        """Transformiere den erfolgreichen Wert via Funktion."""
        return Ok(f(self.value))

    def bind[U, E](self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Verkette eine Funktion, die selbst Result[U, E] zurückgibt."""
        return f(self.value)

    def map_err[E, F](self, _: Callable[[E], F]) -> Ok[T]:
        """Ignoriere die Fehler-Transformation (es liegt kein Fehler vor)."""
        return self

    async def inspect_async(self, f: Callable[[T], Awaitable[object]]) -> Ok[T]:
        """Loese eine Nebenwirkung auf dem Erfolgs-Wert aus und gib das Result unveraendert zurueck.

        Der Unterschied zu `map`/`bind`: die Kette bleibt stehen. `f` darf den
        Wert lesen, aber weder ersetzen noch den Ausgang aendern - das macht
        genau die Faelle ausdrueckbar, in denen ein Erfolg nach aussen gemeldet
        werden muss, ohne dass die Meldung selbst zum Ergebnis wird.

        Der Rueckgabewert von `f` wird bewusst verworfen. Waere er von Belang,
        waere `bind` das richtige Werkzeug.
        """
        await f(self.value)
        return self


@final
@dataclass(frozen=True, slots=True)
class Err[E]:
    """Fehlschlag-Ausgang mit Fehler."""

    error: E

    def map[T, U](self, _: Callable[[T], U]) -> Err[E]:
        """Ignoriere den Fehler (Transformation auf Erfolgs-Wert nicht möglich)."""
        return self

    def bind[T, U](self, _: Callable[[T], Result[U, E]]) -> Err[E]:
        """Ignoriere den Fehler (Verkettung nicht möglich)."""
        return self

    def map_err[F](self, f: Callable[[E], F]) -> Err[F]:
        """Transformiere den Fehler - z. B. Domänenfehler in eine Anzeigemeldung."""
        return Err(f(self.error))

    async def inspect_async[T](self, _: Callable[[T], Awaitable[object]]) -> Err[E]:
        """Loese keine Nebenwirkung aus (es liegt kein Erfolgs-Wert vor)."""
        return self


type Result[T, E] = Ok[T] | Err[E]
