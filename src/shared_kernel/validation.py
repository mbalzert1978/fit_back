"""Collect-all Rule Pattern fuer die Eingabe-Validierung an public Grenzen.

Die Gegenstueck-Form - fail-fast mit genau einem typisierten Domaenenfehler -
ist bereits `Result[T, E]` aus `result.py`; sie braucht hier nichts Eigenes
(.rules/python/python-rule-pattern.md).

Bewusst hier und nicht im Feature: eine feature-lokale Kopie dieses Typs waere
genau das strukturelle Duplikat, das die Regel verbietet. Modul ist stdlib-rein.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import final

__all__ = ["FieldError", "Rule", "all_of", "group_by_field"]


@final
@dataclass(frozen=True, slots=True)
class FieldError:
    """Ein Feldfehler mit typisierter Nutzlast statt vorformatiertem Text.

    `field` traegt den Namen so, wie ihn der API-Vertrag nach aussen zeigt -
    er landet unveraendert im `errors`-Objekt der RFC-7807-Antwort.
    """

    field: str
    message: str


type Rule[T] = Callable[[T], list[FieldError]]


def all_of[T](*rules: Rule[T]) -> Rule[T]:
    """Verknuepfe Regeln so, dass **alle** laufen und alle Meldungen anfallen.

    Bewusst kein Kurzschluss: der Aufrufer soll saemtliche fehlerhaften Felder
    auf einmal gemeldet bekommen, nicht nur das erste.
    """

    def combined(value: T) -> list[FieldError]:
        return [error for rule in rules for error in rule(value)]

    return combined


def group_by_field(errors: Iterable[FieldError]) -> Mapping[str, tuple[str, ...]]:
    """Fasse Feldfehler zur `errors`-Struktur des RFC-7807-Formats zusammen."""
    grouped: dict[str, tuple[str, ...]] = {}
    for error in errors:
        grouped[error.field] = (*grouped.get(error.field, ()), error.message)
    return grouped
