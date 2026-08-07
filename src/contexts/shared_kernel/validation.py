"""Das Rule Pattern in seinen beiden Formen (.rules/python/python-rule-pattern.md).

Die Wahl trifft die **Fehlerform**, nicht die Gewohnheit:

- **Collect-all** (`Rule[T]`, `all_of`) - viele unabhaengige Feldfehler, gemeinsam
  berichtet. Ort: Eingabe-Validierung an der public Grenze eines Use Case.
- **Fail-fast** (`ResultRule[T, E]`, `chain`) - genau ein typisierter Fehler, der
  erste gewinnt und die folgenden Regeln laufen gar nicht mehr. Ort: der
  `parse`-Weg eines Value Object und Domaeneninvarianten.

Bewusst hier und nicht im Feature: eine feature-lokale Kopie dieser Typen waere
genau das strukturelle Duplikat, das die Regel verbietet. Modul ist stdlib-rein.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import final

from src.contexts.shared_kernel.result import Ok, Result

__all__ = [
    "FieldError",
    "FieldErrorDetail",
    "ResultRule",
    "Rule",
    "all_of",
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


type ResultRule[T, E] = Callable[[T], Result[T, E]]


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
