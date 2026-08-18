"""Die Naht der Pipeline: ein Handler, umschlossen von einer Kette gleichgeformter Behaviors.

Ein **Handler** beantwortet die fachliche Frage eines Use Case; ein **Behavior**
sitzt davor und dahinter, ruft den naechsten Schritt selbst - oder eben nicht -
und traegt dieselbe Signatur wie das, was es umschliesst. Daraus folgen die
beiden Eigenschaften, um die es geht: **Reihenfolge** (das erste Behavior ist das
aeusserste) und **Abkuerzen** (wer `Err` liefert, ohne den naechsten Schritt zu
rufen, beendet den Durchlauf).

Dieses Modul beantwortet **nur**, wie eine Kette gefaltet und gerufen wird - kein
einziges konkretes Behavior. Die liegen je Aufgabe in einer eigenen Einheit unter
[`behaviors/`](./behaviors/) und haengen von hier ab, nicht umgekehrt: sonst
zoege jedes weitere Querschnitts-Behavior (Transaktionsklammer, Idempotenz,
Messung, Logging) eine weitere Abhaengigkeit in die Naht, die alle teilen.

Bewusst **nur stdlib**.
"""

from collections.abc import Awaitable, Callable

from src.contexts.shared_kernel.result import Result

__all__ = ["Behavior", "Handler", "build_pipeline"]


type Handler[TIn, TOut, E] = Callable[[TIn], Awaitable[Result[TOut, E]]]
"""Ein Schritt der Kette: Eingabe hinein, `Result` heraus."""

type Behavior[TIn, TOut, E] = Callable[[TIn, Handler[TIn, TOut, E]], Awaitable[Result[TOut, E]]]
"""Ein Handler, der den naechsten Handler bekommt - und selbst entscheidet, ob er ihn ruft."""


def build_pipeline[TIn, TOut, E](
    handler: Handler[TIn, TOut, E], *behaviors: Behavior[TIn, TOut, E]
) -> Handler[TIn, TOut, E]:
    """Lege die Behaviors um den Handler; das **erste** liegt aussen.

    Von innen nach aussen gefaltet, damit die Aufrufreihenfolge die
    Argumentreihenfolge ist: `build_pipeline(h, a, b)` laeuft `a` -> `b` -> `h`.
    Das Ergebnis ist selbst wieder ein `Handler` und laesst sich erneut
    umschliessen - eine Kette und keine Sonderform.
    """
    chained = handler
    for behavior in reversed(behaviors):
        chained = _around(behavior, chained)
    return chained


def _around[TIn, TOut, E](
    behavior: Behavior[TIn, TOut, E], inner: Handler[TIn, TOut, E]
) -> Handler[TIn, TOut, E]:
    """Binde ein Behavior an den Schritt, den es umschliesst.

    Eigene Funktion und keine Closure in der Schleife: sonst faenden alle
    erzeugten Handler am Ende dasselbe, zuletzt zugewiesene `behavior` vor.
    """

    async def run(request: TIn) -> Result[TOut, E]:
        return await behavior(request, inner)

    return run
