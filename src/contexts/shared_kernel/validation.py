"""Das Rule Pattern in seinen beiden Formen (.rules/python/python-rule-pattern.md)."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import final

from src.contexts.shared_kernel.result import Ok, Result

__all__ = [
    "AsyncRule",
    "FieldError",
    "FieldErrorDetail",
    "ParseRule",
    "ResultRule",
    "Rule",
    "all_of",
    "all_of_async",
    "any_of",
    "as_async",
    "chain",
    "group_by_field",
]


type FieldErrorDetail = tuple[str, Mapping[str, object]]
"""Ein Fehlercode mit seinen Parametern - wird am HTTP-Rand uebersetzt."""


@final
@dataclass(frozen=True, slots=True)
class FieldError:
    """Ein Feldfehler mit typisiertem Code und Parametern statt vorformatiertem Text."""

    field: str
    error_code: str
    parameters: Mapping[str, object]


type Rule[T] = Callable[[T], list[FieldError]]


def all_of[T](*rules: Rule[T]) -> Rule[T]:
    """Verknuepfe Regeln so, dass alle laufen und alle Meldungen anfallen."""

    def combined(value: T) -> list[FieldError]:
        return [error for rule in rules for error in rule(value)]

    return combined


type AsyncRule[T] = Callable[[T], Awaitable[list[FieldError]]]
"""Dieselbe Collect-all-Frage fuer eine Regel, die IO braucht."""


def all_of_async[T](*rules: AsyncRule[T]) -> AsyncRule[T]:
    """Verknuepfe asynchrone Regeln so, dass alle laufen und alle Meldungen anfallen.

    Gemeldet wird in der Reihenfolge der Regeln - die gehoert dem Aufrufer, nicht dem
    Scheduler.
    """

    async def combined(value: T) -> list[FieldError]:
        async with asyncio.TaskGroup() as group:
            running = [group.create_task(_as_coroutine(rule, value)) for rule in rules]
        return [error for task in running for error in task.result()]

    return combined


async def _as_coroutine[T](rule: AsyncRule[T], value: T) -> list[FieldError]:
    """Fuehre eine Regel so aus, dass eine echte Coroutine dabei herauskommt.

    `TaskGroup.create_task` nimmt eine Coroutine, `AsyncRule` verspricht nur ein
    `Awaitable`; dieses `await` schliesst die Luecke.
    """
    return await rule(value)


def as_async[T](rule: Rule[T]) -> AsyncRule[T]:
    """Hebe eine synchrone Regel in die asynchrone Form."""

    async def lifted(value: T) -> list[FieldError]:
        return rule(value)

    return lifted


type ParseRule[TIn, TOut, E] = Callable[[TIn], Result[TOut, E]]
"""Eine Regel, die den Wert dabei in seine gueltige Form ueberfuehrt (`str -> UUID`)."""

type ResultRule[T, E] = ParseRule[T, T, E]
"""Der wertformerhaltende Sonderfall - und nur der ist verkettbar."""


def chain[T, E](*rules: ResultRule[T, E]) -> ResultRule[T, E]:
    """Verknuepfe Regeln fail-fast: die naechste laeuft nur nach einem `Ok`."""

    def combined(value: T) -> Result[T, E]:
        result: Result[T, E] = Ok(value)
        for rule in rules:
            result = result.bind(rule)
        return result

    return combined


def any_of[T, E](first: ResultRule[T, E], *rest: ResultRule[T, E]) -> ResultRule[T, E]:
    """Verknuepfe Regeln mit ODER: die erste, die `Ok` meldet, gewinnt.

    Scheitern alle Zweige, ueberlebt der Fehler des letzten; den ehrlichen Fall setzt der
    Aufrufer per `map_err`
    (`docs/decisions/2026-08-07-1331-or-und-conditional-rule-erst-beim-ersten-fall.md`).
    """

    def combined(value: T) -> Result[T, E]:
        outcome = first(value)
        for rule in rest:
            outcome = outcome.or_else(lambda _, rule=rule: rule(value))
        return outcome

    return combined


def group_by_field(errors: Iterable[FieldError]) -> Mapping[str, tuple[FieldErrorDetail, ...]]:
    """Fasse Feldfehler zur `errors`-Struktur des RFC-7807-Formats zusammen."""
    grouped: dict[str, tuple[FieldErrorDetail, ...]] = {}
    for error in errors:
        detail: FieldErrorDetail = (error.error_code, error.parameters)
        grouped[error.field] = (*grouped.get(error.field, ()), detail)
    return grouped
