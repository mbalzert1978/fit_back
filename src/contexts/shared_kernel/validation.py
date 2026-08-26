"""Das Rule Pattern in seinen beiden Formen (.rules/python/python-rule-pattern.md).

Die Wahl trifft die **Fehlerform**, nicht die Gewohnheit:

- **Collect-all** (`Rule[T]`, `all_of`) - viele unabhaengige Feldfehler, gemeinsam
  berichtet. Ort: Eingabe-Validierung an der public Grenze eines Use Case.
- **Fail-fast** (`ResultRule[T, E]`, `chain`) - genau ein typisierter Fehler, der
  erste gewinnt und die folgenden Regeln laufen gar nicht mehr. Ort: der
  `parse`-Weg eines Value Object und Domaeneninvarianten.

`chain` verknuepft diese Regeln mit UND, `any_of` mit ODER - beides ueber
`Result`, nicht ueber `if`.

Bewusst hier und nicht im Feature: eine feature-lokale Kopie dieser Typen waere
genau das strukturelle Duplikat, das die Regel verbietet. Modul ist stdlib-rein.
"""

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
    """Ein Feldfehler mit typisiertem Code und Parametern statt vorformatiertem Text.

    `field` traegt den Namen so, wie ihn der API-Vertrag nach aussen zeigt -
    er landet unveraendert im `errors`-Objekt der RFC-7807-Antwort.
    `error_code` ist sprachunabhaengig und wird erst am HTTP-Rand uebersetzt.
    `parameters` traegt die Werte, die die Vorlage braucht (z.B. Maximalwert).
    """

    field: str
    error_code: str
    parameters: Mapping[str, object]


type Rule[T] = Callable[[T], list[FieldError]]


def all_of[T](*rules: Rule[T]) -> Rule[T]:
    """Verknuepfe Regeln so, dass **alle** laufen und alle Meldungen anfallen.

    Bewusst kein Kurzschluss: der Aufrufer soll saemtliche fehlerhaften Felder
    auf einmal gemeldet bekommen, nicht nur das erste.
    """

    def combined(value: T) -> list[FieldError]:
        return [error for rule in rules for error in rule(value)]

    return combined


type AsyncRule[T] = Callable[[T], Awaitable[list[FieldError]]]
"""Dieselbe Collect-all-Frage, nur mit einer Antwort, auf die man warten muss.

Eine Regel, die IO braucht - Nachschlagen in einer Referenzliste, Rueckfrage bei
einem fremden Context ueber einen Port -, ist als `Rule[T]` nicht formulierbar
und wandert sonst zwangslaeufig in den Handler, wo sie niemand mehr als Regel
wiederfindet. Kein Cancellation-Token daneben: `asyncio` propagiert den Abbruch
ueber `CancelledError` von selbst (.rules/python/python-async.md).
"""


def all_of_async[T](*rules: AsyncRule[T]) -> AsyncRule[T]:
    """Verknuepfe asynchrone Regeln so, dass **alle** laufen und alle Meldungen anfallen.

    Nebenlaeufig ueber eine `TaskGroup` und nicht nacheinander: die Regeln sind
    unabhaengig voneinander, und genau dafuer gibt es strukturierte
    Nebenlaeufigkeit (.rules/python/python-async.md). Gemeldet wird trotzdem in
    der Reihenfolge der Regeln - die Reihenfolge der Antwort gehoert dem
    Aufrufer, nicht dem Scheduler.
    """

    async def combined(value: T) -> list[FieldError]:
        async with asyncio.TaskGroup() as group:
            running = [group.create_task(_as_coroutine(rule, value)) for rule in rules]
        return [error for task in running for error in task.result()]

    return combined


async def _as_coroutine[T](rule: AsyncRule[T], value: T) -> list[FieldError]:
    """Fuehre eine Regel so aus, dass eine echte Coroutine dabei herauskommt.

    `TaskGroup.create_task` nimmt eine Coroutine, `AsyncRule` verspricht nur ein
    `Awaitable` - und das ist die weitere Zusage: eine Regel darf auch ein Objekt
    mit `__await__` zurueckgeben. Statt die Zusage zum Aufrufer hin zu verengen,
    wird hier gewartet; dieses `await` ist die Coroutine, die die `TaskGroup`
    verlangt. Die Regel selbst laeuft dadurch weder frueher noch spaeter.
    """
    return await rule(value)


def as_async[T](rule: Rule[T]) -> AsyncRule[T]:
    """Hebe eine synchrone Regel in die asynchrone Form.

    Eine Regel ohne IO wird davon nicht besser - sie wird nur anschlussfaehig an
    eine Kette, die warten kann. Deshalb hebt diese Funktion und macht keine
    Regel async, die es nicht ist.
    """

    async def lifted(value: T) -> list[FieldError]:
        return rule(value)

    return lifted


type ParseRule[TIn, TOut, E] = Callable[[TIn], Result[TOut, E]]
"""Eine Regel, die den Wert dabei in seine gueltige Form ueberfuehrt (`str -> UUID`).

Die Pruefung *ist* hier die Umwandlung. Nicht verkettbar: `chain`/`any_of`
setzen gleiche Ein- und Ausgangsform voraus.
"""

type ResultRule[T, E] = ParseRule[T, T, E]
"""Der wertformerhaltende Sonderfall - und nur der ist verkettbar."""


def chain[T, E](*rules: ResultRule[T, E]) -> ResultRule[T, E]:
    """Verknuepfe Regeln fail-fast: die naechste laeuft nur nach einem `Ok`.

    Der zurueckgegebene `Result` traegt den einen aufgetretenen Fehler bereits in
    sich - es braucht keine zweite Auswertung, um herauszufinden, welche Regel
    gescheitert ist.
    """

    def combined(value: T) -> Result[T, E]:
        result: Result[T, E] = Ok(value)
        for rule in rules:
            result = result.bind(rule)
        return result

    return combined


def any_of[T, E](first: ResultRule[T, E], *rest: ResultRule[T, E]) -> ResultRule[T, E]:
    """Verknuepfe Regeln mit ODER: die erste, die `Ok` meldet, gewinnt.

    Die Reihenfolge ist fachlich - wer zuerst steht, entscheidet, als was ein
    mehrdeutiger Wert gelesen wird.

    Scheitern alle Zweige, ueberlebt der Fehler des letzten. Das ist **keine**
    Aussage: den ehrlichen Fall setzt der Aufrufer per `map_err`
    (`docs/decisions/2026-08-07-1331-or-und-conditional-rule-erst-beim-ersten-fall.md`).

    `first` steht als eigener Parameter, weil ODER kein neutrales Element hat.
    """

    def combined(value: T) -> Result[T, E]:
        outcome = first(value)
        for rule in rest:
            outcome = outcome.or_else(lambda _, rule=rule: rule(value))
        return outcome

    return combined


def group_by_field(errors: Iterable[FieldError]) -> Mapping[str, tuple[FieldErrorDetail, ...]]:
    """Fasse Feldfehler zur `errors`-Struktur des RFC-7807-Formats zusammen.

    Jeder Feldfehler wird als Tuple aus (error_code, parameters) erfasst,
    zur Uebersetzung bereit fuer den HTTP-Rand.
    """
    grouped: dict[str, tuple[FieldErrorDetail, ...]] = {}
    for error in errors:
        detail: FieldErrorDetail = (error.error_code, error.parameters)
        grouped[error.field] = (*grouped.get(error.field, ()), detail)
    return grouped
