"""Result[T, E] — Basistyp für Operationen mit Erfolgs- oder Fehlschlag-Ausgang.

`Ok`/`Err` tragen den fertigen Ausgang, `AsyncResult` den noch nicht erwarteten;
siehe docs/decisions/2026-08-26-1500-async-result-die-kette-bleibt-chainbar.md.
"""

from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass
from typing import Final, final

type _Unit = object
"""Der Rueckgabewert, den niemand liest - `()` aus Rust.

`object` und nicht `Any`: `Any` schaltet jede Pruefung ab, `object` verbietet
jeden Zugriff auf den Wert.
"""


async def _ready[T, E](outcome: Result[T, E]) -> Result[T, E]:
    """Bringe einen fertigen Ausgang in die Form eines Awaitable."""
    return outcome


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

    def zip[U, E](self, other: Result[U, E], /) -> Result[tuple[T, U], E]:
        """Bei Verkettung bleibt es paarweise: `a.zip(b).zip(c)` traegt `((A, B), C)`."""
        return other.map(lambda value: (self.value, value))

    def zip_all[U, E](self, other: Result[U, list[E]], /) -> Result[tuple[T, U], list[E]]:
        """Wie `zip`, aber der zweite Fehler geht nicht verloren.

        Auf dem Erfolgs-Zweig ist Sammeln dasselbe wie Paaren; getrennt sind die
        beiden nur im Fehlerkanal, und der steht in der Signatur.
        """
        return self.zip(other)

    def bind[U, E](self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Verkette eine Funktion, die selbst Result[U, E] zurückgibt."""
        return f(self.value)

    def bind_async[U, E](self, f: Callable[[T], Awaitable[Result[U, E]]], /) -> AsyncResult[U, E]:
        """Verkette eine **asynchrone** Funktion, die selbst `Result[U, E]` zurueckgibt."""

        async def run() -> Result[U, E]:
            return await f(self.value)

        return AsyncResult(run())

    def map_err[E, F](self, _: Callable[[E], F], /) -> Ok[T]:
        """Ignoriere die Fehler-Transformation (es liegt kein Fehler vor)."""
        return self

    def map_err_async[E, F](self, _: Callable[[E], Awaitable[F]], /) -> AsyncResult[T, F]:
        """Ignoriere die asynchrone Fehler-Transformation (es liegt kein Fehler vor)."""
        return AsyncResult(_ready(self))

    def or_else[U, F, G](self, _: Callable[[F], Result[U, G]], /) -> Ok[T]:
        """Nimm die Alternative nicht (es liegt kein Fehler vor)."""
        return self

    def or_else_async[U, F, G](
        self, _: Callable[[F], Awaitable[Result[U, G]]], /
    ) -> AsyncResult[T, G]:
        """Nimm die asynchrone Alternative nicht (es liegt kein Fehler vor)."""
        return AsyncResult(_ready(self))

    def fold[U, E](self, on_ok: Callable[[T], U], _on_err: Callable[[E], U], /) -> U:
        """Nimm den Erfolgs-Arm - der Fehler-Arm wird nie aufgerufen."""
        return on_ok(self.value)

    async def fold_async[U, E](
        self, on_ok: Callable[[T], Awaitable[U]], _on_err: Callable[[E], Awaitable[U]], /
    ) -> U:
        """Nimm den asynchronen Erfolgs-Arm - der Fehler-Arm wird nie aufgerufen."""
        return await on_ok(self.value)

    def inspect_async[E](self, f: Callable[[T], Awaitable[_Unit]], /) -> AsyncResult[T, E]:
        """Loese eine Nebenwirkung auf dem Erfolgs-Wert aus."""

        async def run() -> Result[T, E]:
            await f(self.value)
            return self

        return AsyncResult(run())


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
        return AsyncResult(_ready(self))

    def zip[U, F](self, _: Result[U, F], /) -> Err[E]:
        """Es liegt schon ein Fehler vor - der zweite Ausgang aendert daran nichts."""
        return self

    def zip_all[X, U](self: Err[list[X]], other: Result[U, list[X]], /) -> Err[list[X]]:
        """Nimm die Fehler des zweiten Ausgangs dazu, statt ihn zu verwerfen."""
        return other.fold(lambda _: self, lambda errors: Err([*self.error, *errors]))

    def bind[T, U, F](self, _: Callable[[T], Result[U, F]], /) -> Err[E]:
        """Ignoriere den Fehler (Verkettung nicht möglich)."""
        return self

    def bind_async[T, U, F](
        self, _: Callable[[T], Awaitable[Result[U, F]]], /
    ) -> AsyncResult[U, E]:
        """Verkette nichts - die uebergebene Coroutine wird nie erzeugt und nie erwartet."""
        return AsyncResult(_ready(self))

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

    def inspect_async[T](self, _: Callable[[T], Awaitable[_Unit]], /) -> AsyncResult[T, E]:
        """Loese keine Nebenwirkung aus (es liegt kein Erfolgs-Wert vor)."""
        return AsyncResult(_ready(self))


type Result[T, E] = Ok[T] | Err[E]


@final
@dataclass(frozen=True, slots=True, eq=False)
class AsyncResult[T, E]:
    """Ein noch nicht erwartetes `Result`, das schon Kombinatoren traegt.

    `eq=False`: eine ausstehende Kette laesst sich nicht sinnvoll vergleichen,
    erst das `Result` danach. Wie jede Coroutine laesst sie sich nur einmal
    erwarten.
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

    def zip[U, F](self, other: Result[U, F], /) -> AsyncResult[tuple[T, U], E | F]:
        """Fuehre diese Kette mit einem fertigen Ausgang zu einem ueber ihrem Paar zusammen."""
        return self._then(lambda outcome: outcome.zip(other))

    def zip_all[V, X, U](
        self: AsyncResult[V, list[X]], other: Result[U, list[X]], /
    ) -> AsyncResult[tuple[V, U], list[X]]:
        """Lege einen fertigen Ausgang neben die Kette und behalte beide Fehler.

        `V` statt des `T` der Klasse - siehe
        docs/decisions/2026-08-26-2330-die-wurzel-sammelt-ihre-befunde-selbst.md.
        """
        return self._then(lambda outcome: outcome.zip_all(other))

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

    def inspect_async(self, f: Callable[[T], Awaitable[_Unit]], /) -> AsyncResult[T, E]:
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
