"""Result[T, E] — Basistyp für Operationen mit Erfolgs- oder Fehlschlag-Ausgang.

`Ok` und `Err` sind kovariant in ihrem Typparameter: eine Regel, die einen engeren
Fehlerfall liefert, passt damit in eine Kette, die den Obertyp verspricht. Zwei Details
tragen das und waeren sonst als Willkuer zu lesen. `Final` auf den Feldern, weil nur ein
nachweislich nur lesbares Feld kovariant sein darf. Und die freien Typparameter in
`Err.bind`, `Err.bind_async` und `Ok.or_else`: sie beschreiben eine Fortsetzung, die
genau diese drei Methoden ohnehin nie aufrufen - stuende dort der Klassen-Typparameter,
saesse er in einer Argument-Position und waere invariant.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Final, final


@final
@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Erfolgreicher Ausgang mit Wert."""

    value: Final[T]

    def map[U](self, f: Callable[[T], U]) -> Ok[U]:
        """Transformiere den erfolgreichen Wert via Funktion."""
        return Ok(f(self.value))

    def bind[U, E](self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Verkette eine Funktion, die selbst Result[U, E] zurückgibt."""
        return f(self.value)

    async def bind_async[U, E](self, f: Callable[[T], Awaitable[Result[U, E]]]) -> Result[U, E]:
        """Verkette eine **asynchrone** Funktion, die selbst `Result[U, E]` zurueckgibt.

        Das async-Gegenstueck zu `bind` und der Grund, warum eine Kette einen
        `async` Handler ueberhaupt aufnehmen kann. Ohne sie muesste der Aufrufer
        den `Result` von Hand aufmachen, um zu entscheiden, ob er das `await`
        ueberhaupt ausloest - und genau dieses `if` ist das, was die
        Behavior-Kette loswerden soll.
        """
        return await f(self.value)

    def map_err[E, F](self, _: Callable[[E], F], /) -> Ok[T]:
        """Ignoriere die Fehler-Transformation (es liegt kein Fehler vor)."""
        return self

    def or_else[U, F](self, _: Callable[[F], Result[U, F]], /) -> Ok[T]:
        """Nimm die Alternative nicht (es liegt kein Fehler vor)."""
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

    error: Final[E]

    def map[T, U](self, _: Callable[[T], U], /) -> Err[E]:
        """Ignoriere den Fehler (Transformation auf Erfolgs-Wert nicht möglich)."""
        return self

    def bind[T, U, F](self, _: Callable[[T], Result[U, F]], /) -> Err[E]:
        """Ignoriere den Fehler (Verkettung nicht möglich)."""
        return self

    async def bind_async[T, U, F](self, _: Callable[[T], Awaitable[Result[U, F]]], /) -> Err[E]:
        """Verkette nichts - die uebergebene Coroutine wird nie erzeugt und nie erwartet.

        Das ist die Abkuerzung, von der die Behavior-Kette lebt: liegt ein Fehler
        vor, laeuft der naechste Schritt gar nicht erst an.
        """
        return self

    def map_err[F](self, f: Callable[[E], F]) -> Err[F]:
        """Transformiere den Fehler - z. B. Domänenfehler in eine Anzeigemeldung."""
        return Err(f(self.error))

    def or_else[T, F](self, f: Callable[[E], Result[T, F]], /) -> Result[T, F]:
        """Versuche die Alternative - das Gegenstueck zu `bind` auf dem Fehler-Zweig."""
        return f(self.error)

    async def inspect_async[T](self, _: Callable[[T], Awaitable[object]], /) -> Err[E]:
        """Loese keine Nebenwirkung aus (es liegt kein Erfolgs-Wert vor)."""
        return self


type Result[T, E] = Ok[T] | Err[E]
