"""Die Pipeline: ein Handler, umschlossen von einer Kette gleichgeformter Behaviors.

Ein **Handler** beantwortet die fachliche Frage eines Use Case; ein **Behavior**
sitzt davor und dahinter, ruft den naechsten Schritt selbst - oder eben nicht -
und traegt dieselbe Signatur wie das, was es umschliesst. Daraus folgen die
beiden Eigenschaften, um die es geht: **Reihenfolge** (das erste Behavior ist das
aeusserste) und **Abkuerzen** (wer `Err` liefert, ohne den naechsten Schritt zu
rufen, beendet den Durchlauf).

Das ist die Stelle, an der alles Querschnittliche landet, sobald es zum zweiten
Mal gebraucht wird - Transaktionsklammer, Idempotenz, Messung, Logging. Heute
haengt genau ein Behavior in der Kette: die Eingabe-Validierung.

Bewusst **nur stdlib** und bewusst **kein** Ersatz fuer `validation.py`: `Rule`,
`all_of`/`all_of_async` und `FieldError` bleiben dort und werden hier nur
benutzt. Dieses Modul weiss, *wann* validiert wird, nicht *was* gilt.
"""

from collections.abc import Awaitable, Callable, Sequence

from src.contexts.shared_kernel.result import Err, Ok, Result
from src.contexts.shared_kernel.validation import AsyncRule, FieldError

__all__ = ["Behavior", "Handler", "build_pipeline", "validating"]


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


def validating[TIn, TOut, E](
    rule: AsyncRule[TIn], on_invalid: Callable[[Sequence[FieldError]], E]
) -> Behavior[TIn, TOut, E]:
    """Baue das Behavior, das die Eingabe prueft, bevor irgendetwas anderes laeuft.

    Es hebt die gesammelten `FieldError` in den **einen** Fehlerkanal der
    Pipeline - `on_invalid` sagt, wie der Fall dieses Use Case dafuer heisst -
    und kuerzt ab. Damit fallen die beiden frueher getrennten Fehlerkanaele
    (Feldfehler hier, Domaenenfehler dort) zusammen und der Slice braucht nur
    noch **einen** Fold am Ende.
    """

    async def behave(request: TIn, inner: Handler[TIn, TOut, E]) -> Result[TOut, E]:
        checked = await _checked(rule, request, on_invalid)
        return await checked.bind_async(inner)

    return behave


async def _checked[TIn, E](
    rule: AsyncRule[TIn], request: TIn, on_invalid: Callable[[Sequence[FieldError]], E]
) -> Result[TIn, E]:
    """Werte das Regelwerk aus und uebersetze sein Urteil in den Fehlerkanal."""
    errors = await rule(request)
    return Err(on_invalid(errors)) if errors else Ok(request)
