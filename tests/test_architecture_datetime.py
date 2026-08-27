"""Architektur-Tests rund um Zeit: kein ungebundenes Ablesen, kein `datetime` in der Domaene.

Zwei Regeln, die leicht verwechselt werden:

1. **Woher** kommt die Zeit? Nie aus `datetime.now()`/`utcnow()` direkt, sondern
   aus dem `TimeProvider` - sonst ist kein Ablauf deterministisch testbar.
2. **Was** haelt die Domaene? Einen `Timestamp` (Unix-Sekunden), nie einen
   `datetime` - siehe docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md.

Sie ueberschneiden sich nicht: ein Aggregat, das einen von aussen gereichten
`datetime` nur *haelt*, ruft nirgends `datetime.now()` auf.
"""

import ast
from collections.abc import Iterator
from typing import Final

from tests.architecture_ast import Befund, modules, no_findings

# Die Schichten, in denen Zeit ausschliesslich als `Timestamp` gefuehrt wird.
# `application` und `api` fehlen bewusst: Response-DTO und Router sind die
# Uebersetzung an den Rand hin, und ISO-8601 auf der Leitung braucht dort
# irgendwann einen `datetime`.
_TIMESTAMP_ONLY_LAYERS: Final = frozenset({"domain", "contracts"})

# Die eine Naht, die die Zeit ablesen darf.
_TIME_PROVIDER_SEAM: Final = "shared_kernel/time_provider.py"

_TZ_KEYWORDS: Final = frozenset({"tz", "tzinfo"})


def _unbound_time_reads(tree: ast.Module) -> Iterator[tuple[int, str]]:
    """Jeder Aufruf, der die Zeit am `TimeProvider` vorbei abliest."""
    for node in ast.walk(tree):
        match node:
            case ast.Call(
                lineno=int() as line,
                func=ast.Attribute(attr="utcnow", value=ast.Name(id="datetime")),
            ):
                yield line, "datetime.utcnow() - nutze TimeProvider.utc_now()"

            case ast.Call(
                lineno=int() as line,
                func=ast.Attribute(attr="now", value=ast.Name(id="datetime")),
                keywords=keywords,
            ) if not any(keyword.arg in _TZ_KEYWORDS for keyword in keywords):
                yield line, "datetime.now() ohne tz-Argument - nutze TimeProvider.utc_now()"


def _signature_annotations(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[tuple[int, ast.expr]]:
    """Rueckgabetyp und jede Parameter-Angabe, `*args` und `**kwargs` eingeschlossen."""
    args = node.args
    places = (
        (node.lineno, node.returns),
        *(
            (argument.lineno, argument.annotation)
            for argument in (
                *args.posonlyargs,
                *args.args,
                *args.kwonlyargs,
                args.vararg,
                args.kwarg,
            )
            if argument is not None
        ),
    )
    return ((line, annotation) for line, annotation in places if annotation is not None)


def _annotations(tree: ast.Module) -> Iterator[tuple[int, ast.expr]]:
    """Jede Typangabe des Moduls samt Zeilennummer.

    Zwei Stellen, an denen ein Typ einen Wert festhaelt: annotierte Zuweisungen
    (Klassen-, Dataclass- und Modulfelder) und Signaturen.
    """
    for node in ast.walk(tree):
        match node:
            case ast.AnnAssign(lineno=int() as line, annotation=ast.expr() as annotation):
                yield line, annotation

            case ast.FunctionDef() | ast.AsyncFunctionDef():
                yield from _signature_annotations(node)


def _names_datetime(annotation: ast.expr) -> bool:
    """Nennt die Typangabe irgendwo `datetime`.

    Auch verschachtelt: `datetime | None`, `list[datetime]` und
    `Mapping[str, datetime]` halten genauso einen fest wie die nackte Angabe.
    """
    return any(_is_datetime(node) for node in ast.walk(annotation))


def _is_datetime(node: ast.AST) -> bool:
    """Erfasst `datetime` und `datetime.datetime` gleichermassen."""
    match node:
        case ast.Name(id="datetime") | ast.Attribute(attr="datetime"):
            return True
        case _:
            return False


def test_die_zeit_wird_nie_am_time_provider_vorbei_abgelesen() -> None:
    no_findings(
        (
            Befund(py_file, line, reason)
            for py_file, tree in modules(
                lambda path: not path.as_posix().endswith(_TIME_PROVIDER_SEAM)
            )
            for line, reason in _unbound_time_reads(tree)
        ),
        "Architektur-Verletzung: datetime-Aufrufe ohne Timezone gefunden:",
    )


def test_die_domaene_haelt_keinen_datetime() -> None:
    """Ein Aggregat, das einen datetime bloss haelt, entgeht dem Test daneben."""
    no_findings(
        (
            Befund(
                py_file,
                line,
                "haelt einen datetime - nutze Timestamp und wandle erst am Rand um",
            )
            for py_file, tree in modules(
                lambda path: bool(_TIMESTAMP_ONLY_LAYERS & set(path.parts))
            )
            for line, annotation in _annotations(tree)
            if _names_datetime(annotation)
        ),
        "Architektur-Verletzung: datetime in der Domaene gefunden:",
    )
