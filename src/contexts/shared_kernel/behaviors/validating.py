"""Das Behavior, das die Eingabe prueft, bevor irgendetwas anderes laeuft.

Weiss, *wann* validiert wird, nicht *was* gilt - Letzteres bleibt in
[`../validation.py`](../validation.py); siehe
docs/decisions/2026-08-17-0937-pipeline-als-behavior-kette-im-shared-kernel.md.
"""

from collections.abc import Callable, Sequence

from src.contexts.shared_kernel.pipeline import Behavior, Handler
from src.contexts.shared_kernel.result import AsyncResult, Err, Ok, Result
from src.contexts.shared_kernel.validation import AsyncRule, FieldError

__all__ = ["validating"]


def validating[TIn, TOut, E](
    rule: AsyncRule[TIn], on_invalid: Callable[[Sequence[FieldError]], E]
) -> Behavior[TIn, TOut, E]:
    """Baue das Behavior, das die Eingabe prueft und bei Verstoss abkuerzt.

    `on_invalid` hebt die gesammelten `FieldError` in den Fehlerkanal dieser Pipeline.
    """

    def behave(request: TIn, inner: Handler[TIn, TOut, E]) -> AsyncResult[TOut, E]:
        return AsyncResult(_checked(rule, request, on_invalid)).bind_async(inner)

    return behave


async def _checked[TIn, E](
    rule: AsyncRule[TIn], request: TIn, on_invalid: Callable[[Sequence[FieldError]], E]
) -> Result[TIn, E]:
    """Werte das Regelwerk aus und uebersetze sein Urteil in den Fehlerkanal."""
    return Err(on_invalid(errors)) if (errors := await rule(request)) else Ok(request)
