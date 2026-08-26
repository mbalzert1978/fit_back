"""Das Behavior, das die Eingabe prueft, bevor irgendetwas anderes laeuft.

Es haengt an beidem: an der Pipeline-Naht ([`../pipeline.py`](../pipeline.py))
fuer die Form eines Behaviors und an [`../validation.py`](../validation.py) fuer
die Regelform. Genau deshalb liegt es hier und nicht in der Naht - die soll von
`validation.py` nichts wissen muessen.

Bewusst **kein** Ersatz fuer `validation.py`: `Rule`, `all_of`/`all_of_async` und
`FieldError` bleiben dort und werden hier nur benutzt. Dieses Modul weiss,
*wann* validiert wird, nicht *was* gilt.
"""

from collections.abc import Callable, Sequence

from src.contexts.shared_kernel.pipeline import Behavior, Handler
from src.contexts.shared_kernel.result import AsyncResult, Err, Ok, Result
from src.contexts.shared_kernel.validation import AsyncRule, FieldError

__all__ = ["validating"]


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

    def behave(request: TIn, inner: Handler[TIn, TOut, E]) -> AsyncResult[TOut, E]:
        return AsyncResult(_checked(rule, request, on_invalid)).bind_async(inner)

    return behave


async def _checked[TIn, E](
    rule: AsyncRule[TIn], request: TIn, on_invalid: Callable[[Sequence[FieldError]], E]
) -> Result[TIn, E]:
    """Werte das Regelwerk aus und uebersetze sein Urteil in den Fehlerkanal."""
    return Err(on_invalid(errors)) if (errors := await rule(request)) else Ok(request)
