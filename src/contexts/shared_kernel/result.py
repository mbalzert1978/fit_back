"""Result[T, E] — Basistyp für Operationen mit Erfolgs- oder Fehlschlag-Ausgang.

`Ok` und `Err` sind kovariant in ihrem Typparameter: eine Regel, die einen engeren
Fehlerfall liefert, passt damit in eine Kette, die den Obertyp verspricht. Zwei Details
tragen das und waeren sonst als Willkuer zu lesen. `Final` auf den Feldern, weil nur ein
nachweislich nur lesbares Feld kovariant sein darf. Und die freien Typparameter ueberall
dort, wo eine Methode ihre Fortsetzung gar nicht erst aufruft (`Err.bind`, `Ok.or_else`
und ihre `_async`-Gegenstuecke): sie beschreiben eine Fortsetzung, die diese Methoden
ohnehin nie rufen - stuende dort der Klassen-Typparameter, saesse er in einer
Argument-Position und waere invariant.

**Zwei Formen, ein Typ.** `Ok`/`Err` tragen den fertigen Ausgang, `AsyncResult` den noch
nicht erwarteten. Jede `_async`-Methode liefert ein `AsyncResult` statt einer nackten
Coroutine; deshalb bleibt eine Kette aus sync- und async-Schritten bis zum Schluss
chainbar und braucht genau ein `await` - am Ende. `AsyncResult` ist keine zweite
Implementierung: es faltet sein Awaitable auf und ruft dieselben `Ok`/`Err`-Methoden.
"""

from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass
from typing import Final, final


def _lifted[T, E](outcome: Result[T, E]) -> AsyncResult[T, E]:
    """Hebe einen fertigen Ausgang in eine bereits abgeschlossene Kette."""

    async def run() -> Result[T, E]:
        return outcome

    return AsyncResult(run())


@final
@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Erfolgreicher Ausgang mit Wert."""

    value: Final[T]

    def map[U](self, f: Callable[[T], U]) -> Ok[U]:
        """Transformiere den erfolgreichen Wert via Funktion."""
        return Ok(f(self.value))

    def map_async[U, E](self, f: Callable[[T], Awaitable[U]], /) -> AsyncResult[U, E]:
        """Transformiere den erfolgreichen Wert via **asynchroner** Funktion."""

        async def run() -> Result[U, E]:
            return Ok(await f(self.value))

        return AsyncResult(run())

    def bind[U, E](self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Verkette eine Funktion, die selbst Result[U, E] zurückgibt."""
        return f(self.value)

    def bind_async[U, E](self, f: Callable[[T], Awaitable[Result[U, E]]], /) -> AsyncResult[U, E]:
        """Verkette eine **asynchrone** Funktion, die selbst `Result[U, E]` zurueckgibt.

        Das async-Gegenstueck zu `bind` und der Grund, warum eine Kette einen
        `async` Handler ueberhaupt aufnehmen kann. Ohne sie muesste der Aufrufer
        den `Result` von Hand aufmachen, um zu entscheiden, ob er das `await`
        ueberhaupt ausloest - und genau dieses `if` ist das, was die
        Behavior-Kette loswerden soll.
        """

        async def run() -> Result[U, E]:
            return await f(self.value)

        return AsyncResult(run())

    def map_err[E, F](self, _: Callable[[E], F], /) -> Ok[T]:
        """Ignoriere die Fehler-Transformation (es liegt kein Fehler vor)."""
        return self

    def map_err_async[E, F](self, _: Callable[[E], Awaitable[F]], /) -> AsyncResult[T, F]:
        """Ignoriere die asynchrone Fehler-Transformation (es liegt kein Fehler vor)."""
        return self._settled()

    def or_else[U, F, G](self, _: Callable[[F], Result[U, G]], /) -> Ok[T]:
        """Nimm die Alternative nicht (es liegt kein Fehler vor)."""
        return self

    def or_else_async[U, F, G](
        self, _: Callable[[F], Awaitable[Result[U, G]]], /
    ) -> AsyncResult[T, G]:
        """Nimm die asynchrone Alternative nicht (es liegt kein Fehler vor)."""
        return self._settled()

    def fold[U, E](self, on_ok: Callable[[T], U], _on_err: Callable[[E], U], /) -> U:
        """Nimm den Erfolgs-Arm - der Fehler-Arm wird nie aufgerufen."""
        return on_ok(self.value)

    async def fold_async[U, E](
        self, on_ok: Callable[[T], Awaitable[U]], _on_err: Callable[[E], Awaitable[U]], /
    ) -> U:
        """Nimm den asynchronen Erfolgs-Arm - der Fehler-Arm wird nie aufgerufen."""
        return await on_ok(self.value)

    def inspect_async[E](self, f: Callable[[T], Awaitable[object]], /) -> AsyncResult[T, E]:
        """Loese eine Nebenwirkung auf dem Erfolgs-Wert aus und gib das Result unveraendert zurueck.

        Der Unterschied zu `map`/`bind`: die Kette bleibt stehen. `f` darf den
        Wert lesen, aber weder ersetzen noch den Ausgang aendern - das macht
        genau die Faelle ausdrueckbar, in denen ein Erfolg nach aussen gemeldet
        werden muss, ohne dass die Meldung selbst zum Ergebnis wird.

        Der Rueckgabewert von `f` wird bewusst verworfen. Waere er von Belang,
        waere `bind` das richtige Werkzeug.
        """

        async def run() -> Result[T, E]:
            await f(self.value)
            return self

        return AsyncResult(run())

    def _settled[E](self) -> AsyncResult[T, E]:
        """Reiche diesen fertigen Erfolg als bereits abgeschlossene Kette weiter."""
        return _lifted(self)


@final
@dataclass(frozen=True, slots=True)
class Err[E]:
    """Fehlschlag-Ausgang mit Fehler."""

    error: Final[E]

    def map[T, U](self, _: Callable[[T], U], /) -> Err[E]:
        """Ignoriere den Fehler (Transformation auf Erfolgs-Wert nicht möglich)."""
        return self

    def map_async[T, U](self, _: Callable[[T], Awaitable[U]], /) -> AsyncResult[U, E]:
        """Ignoriere den Fehler (asynchrone Transformation nicht möglich)."""
        return self._settled()

    def bind[T, U, F](self, _: Callable[[T], Result[U, F]], /) -> Err[E]:
        """Ignoriere den Fehler (Verkettung nicht möglich)."""
        return self

    def bind_async[T, U, F](
        self, _: Callable[[T], Awaitable[Result[U, F]]], /
    ) -> AsyncResult[U, E]:
        """Verkette nichts - die uebergebene Coroutine wird nie erzeugt und nie erwartet.

        Das ist die Abkuerzung, von der die Behavior-Kette lebt: liegt ein Fehler
        vor, laeuft der naechste Schritt gar nicht erst an.
        """
        return self._settled()

    def map_err[F](self, f: Callable[[E], F]) -> Err[F]:
        """Transformiere den Fehler - z. B. Domänenfehler in eine Anzeigemeldung."""
        return Err(f(self.error))

    def map_err_async[T, F](self, f: Callable[[E], Awaitable[F]], /) -> AsyncResult[T, F]:
        """Transformiere den Fehler via **asynchroner** Funktion."""

        async def run() -> Result[T, F]:
            return Err(await f(self.error))

        return AsyncResult(run())

    def or_else[T, F](self, f: Callable[[E], Result[T, F]], /) -> Result[T, F]:
        """Versuche die Alternative - das Gegenstueck zu `bind` auf dem Fehler-Zweig."""
        return f(self.error)

    def or_else_async[T, F](
        self, f: Callable[[E], Awaitable[Result[T, F]]], /
    ) -> AsyncResult[T, F]:
        """Versuche die **asynchrone** Alternative - `bind_async` auf dem Fehler-Zweig."""

        async def run() -> Result[T, F]:
            return await f(self.error)

        return AsyncResult(run())

    def fold[T, U](self, _on_ok: Callable[[T], U], on_err: Callable[[E], U], /) -> U:
        """Nimm den Fehler-Arm - der Erfolgs-Arm wird nie aufgerufen."""
        return on_err(self.error)

    async def fold_async[T, U](
        self, _on_ok: Callable[[T], Awaitable[U]], on_err: Callable[[E], Awaitable[U]], /
    ) -> U:
        """Nimm den asynchronen Fehler-Arm - der Erfolgs-Arm wird nie aufgerufen."""
        return await on_err(self.error)

    def inspect_async[T](self, _: Callable[[T], Awaitable[object]], /) -> AsyncResult[T, E]:
        """Loese keine Nebenwirkung aus (es liegt kein Erfolgs-Wert vor)."""
        return self._settled()

    def _settled[T](self) -> AsyncResult[T, E]:
        """Reiche diesen fertigen Fehlschlag als bereits abgeschlossene Kette weiter."""
        return _lifted(self)


type Result[T, E] = Ok[T] | Err[E]


@final
@dataclass(frozen=True, slots=True, eq=False)
class AsyncResult[T, E]:
    """Ein noch nicht erwartetes `Result`, das trotzdem schon Kombinatoren traegt.

    Der Grund, warum eine Kette kein `await` in der Mitte braucht: jeder Schritt
    gibt wieder ein `AsyncResult` zurueck, und erst der Aufrufer loest die
    ganze Kette mit **einem** `await` aus.

    ```python
    await AsyncResult(pending).map(lambda v: v * 2).bind_async(next_step)
    ```

    `Ok`/`Err` bleiben der einzige Ort, an dem der Ausgang entschieden wird -
    jede Methode hier reicht ihren Schritt an `_then` bzw. `_then_async` weiter,
    und die falten das Awaitable auf und rufen die gleichnamige Methode darauf.
    Auch der Kurzschluss ist damit derselbe: liegt ein `Err` vor, laeuft kein
    weiterer Schritt an.

    `eq=False`, weil ein Vergleich zweier ausstehender Ketten nichts aussagt;
    verglichen wird das `Result` **nach** dem `await`. Und wie jede Coroutine
    laesst sich eine Kette nur **einmal** erwarten.
    """

    awaitable: Final[Awaitable[Result[T, E]]]

    def __await__(self) -> Generator[object, None, Result[T, E]]:
        """Loese die ganze Kette aus und liefere den fertigen Ausgang."""
        return self.awaitable.__await__()

    def _then[U, F](self, step: Callable[[Result[T, E]], Result[U, F]], /) -> AsyncResult[U, F]:
        """Haenge einen **synchronen** Schritt hinten an die Kette."""

        async def run() -> Result[U, F]:
            return step(await self.awaitable)

        return AsyncResult(run())

    def _then_async[U, F](
        self, step: Callable[[Result[T, E]], Awaitable[Result[U, F]]], /
    ) -> AsyncResult[U, F]:
        """Haenge einen **asynchronen** Schritt hinten an die Kette."""

        async def run() -> Result[U, F]:
            return await step(await self.awaitable)

        return AsyncResult(run())

    def map[U](self, f: Callable[[T], U], /) -> AsyncResult[U, E]:
        """Transformiere den erfolgreichen Wert via Funktion."""
        return self._then(lambda outcome: outcome.map(f))

    def map_async[U](self, f: Callable[[T], Awaitable[U]], /) -> AsyncResult[U, E]:
        """Transformiere den erfolgreichen Wert via **asynchroner** Funktion."""
        return self._then_async(lambda outcome: outcome.map_async(f))

    def bind[U, F](self, f: Callable[[T], Result[U, F]], /) -> AsyncResult[U, E | F]:
        """Verkette eine Funktion, die selbst `Result[U, F]` zurueckgibt."""
        return self._then(lambda outcome: outcome.bind(f))

    def bind_async[U, F](
        self, f: Callable[[T], Awaitable[Result[U, F]]], /
    ) -> AsyncResult[U, E | F]:
        """Verkette eine **asynchrone** Funktion, die selbst `Result[U, F]` zurueckgibt."""
        return self._then_async(lambda outcome: outcome.bind_async(f))

    def map_err[F](self, f: Callable[[E], F], /) -> AsyncResult[T, F]:
        """Transformiere den Fehler."""
        return self._then(lambda outcome: outcome.map_err(f))

    def map_err_async[F](self, f: Callable[[E], Awaitable[F]], /) -> AsyncResult[T, F]:
        """Transformiere den Fehler via **asynchroner** Funktion."""
        return self._then_async(lambda outcome: outcome.map_err_async(f))

    def or_else[U, F](self, f: Callable[[E], Result[U, F]], /) -> AsyncResult[T | U, F]:
        """Versuche die Alternative auf dem Fehler-Zweig."""
        return self._then(lambda outcome: outcome.or_else(f))

    def or_else_async[U, F](
        self, f: Callable[[E], Awaitable[Result[U, F]]], /
    ) -> AsyncResult[T | U, F]:
        """Versuche die **asynchrone** Alternative auf dem Fehler-Zweig."""
        return self._then_async(lambda outcome: outcome.or_else_async(f))

    def inspect_async(self, f: Callable[[T], Awaitable[object]], /) -> AsyncResult[T, E]:
        """Loese eine Nebenwirkung auf dem Erfolgs-Wert aus, ohne die Kette zu veraendern."""
        return self._then_async(lambda outcome: outcome.inspect_async(f))

    async def fold[U](self, on_ok: Callable[[T], U], on_err: Callable[[E], U], /) -> U:
        """Fuehre die Kette aus und falte ihren Ausgang auf einen Wert - der Ausgang der Kette."""
        return (await self.awaitable).fold(on_ok, on_err)

    async def fold_async[U](
        self, on_ok: Callable[[T], Awaitable[U]], on_err: Callable[[E], Awaitable[U]], /
    ) -> U:
        """Falte den Ausgang der Kette mit **asynchronen** Armen auf einen Wert."""
        return await (await self.awaitable).fold_async(on_ok, on_err)
