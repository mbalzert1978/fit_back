"""Der Vertrag, den jeder Fehlerfall erfuellt: er traegt seinen Code selbst.

Entscheidung: docs/decisions/2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md
"""

from dataclasses import fields, is_dataclass
from types import UnionType
from typing import ClassVar, Protocol, get_args, runtime_checkable

__all__ = ["CodedError", "codes_of", "error_cases", "parameters_of"]


@runtime_checkable
class CodedError(Protocol):
    """Ein Fehlerfall, der seinen Code kennt."""

    code: ClassVar[str]


def error_cases(*unions: object) -> tuple[type, ...]:
    """Zaehle die Faelle einer oder mehrerer Fehler-Unions auf, verschachtelt aufgeloest.

    Ein einzelner, nicht-unionierter Typ ist eine Union mit einem Fall und wird
    genauso behandelt - der Aufrufer muss nicht wissen, welche Form er hat.
    """
    collected: list[type] = []
    for union in unions:
        collected.extend(_flatten(union))
    # Reihenfolge erhalten, Duplikate raus: derselbe Fall kann ueber zwei Wege
    # erreichbar sein, gemeldet werden soll er einmal.
    return tuple(dict.fromkeys(collected))


def _flatten(union: object) -> list[type]:
    """Loese einen Typ-Alias oder eine Union bis auf ihre Klassen auf."""
    if (value := getattr(union, "__value__", None)) is not None:
        # PEP-695-Alias (`type X = A | B`) - erst auf seinen Wert schauen.
        return _flatten(value)
    if isinstance(union, UnionType) or get_args(union):
        return [case for arg in get_args(union) for case in _flatten(arg)]
    return [union] if isinstance(union, type) else []


def codes_of(*unions: object) -> dict[str, type]:
    """Bilde Code -> Fehlerfall ueber alle Faelle der uebergebenen Unions.

    Wirft `ValueError`, wenn ein Fall keinen Code traegt oder zwei Faelle sich
    denselben Code teilen - siehe
    docs/decisions/2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md.
    """
    by_code: dict[str, type] = {}
    uncoded: list[str] = []

    for case in error_cases(*unions):
        code = getattr(case, "code", None)
        if not isinstance(code, str) or not code:
            uncoded.append(case.__name__)
            continue
        if (owner := by_code.get(code)) is not None:
            msg = f"Fehlercode {code!r} doppelt vergeben: {owner.__name__} und {case.__name__}"
            raise ValueError(msg)
        by_code[code] = case

    if uncoded:
        msg = (
            f"Fehlerfaelle ohne `code`: {sorted(uncoded)}. "
            "Jeder Fall erfuellt das CodedError-Protocol aus dem Shared Kernel."
        )
        raise ValueError(msg)

    return by_code


def parameters_of(case: type) -> frozenset[str]:
    """Nenne die Felder, die ein Fehlerfall als Nutzlast traegt.

    Das ist die Menge, aus der eine Textvorlage ihre Platzhalter fuellen darf. Ein
    Fall ohne Nutzlast (`PasswordHashIsEmpty`) liefert die leere Menge - seine
    Vorlage darf dann keinen Platzhalter haben.
    """
    if not is_dataclass(case):
        return frozenset()
    return frozenset(field.name for field in fields(case))
