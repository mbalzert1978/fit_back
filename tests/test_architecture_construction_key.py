"""Architektur-Test: wer einen Rohwert haelt, haelt auch einen `ConstructionKey`.

Die Sperre aus `shared_kernel/construction.py` besteht je Typ aus drei Teilen -
dem modul-privaten `_KEY`, dem `key`-Feld und dem `deny_foreign_key` im
`__post_init__`. Ein vergessener Teil faellt nirgends auf: der rohe Konstruktor
geht dann einfach durch, wie `Email("quatsch")` es vor
docs/decisions/2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md tat.

Gesucht wird in jedem `value_objects/` - der Ordner sagt, welche Typen Value
Objects sind, nicht welche die Sperre brauchen. Das entscheidet der Rohwert: ein
Feld mit primitivem Typ haelt eine Regel, die niemand geprueft hat. Eine Tagged
Union ohne Feld (`German`, `Active`) hat keinen Rohwert; `PendingDeletion` traegt
einen `Timestamp`, also einen bereits gepruefen Typ. Beide bleiben befreit.

Gelesen wird der Quelltext und nicht das importierte Modul: `_KEY` ist
modul-privat, und eine Pruefung ueber `getattr` griffe an dem Namen vorbei, um
den es geht.
"""

import ast
from collections.abc import Iterator
from typing import Final

from tests.architecture_ast import Befund, modules, no_findings

_VALUE_OBJECT_DIR: Final = "value_objects"

_PRIMITIVES: Final = frozenset({"str", "int", "float", "bool", "bytes", "UUID"})
"""Die Feldtypen, die einen ungepruefen Rohwert bedeuten."""


def _classes(tree: ast.Module) -> Iterator[ast.ClassDef]:
    """Jede Klasse des Moduls, auch eine verschachtelte."""
    for node in ast.walk(tree):
        match node:
            case ast.ClassDef():
                yield node


def _fields(klasse: ast.ClassDef) -> Iterator[tuple[str, ast.expr]]:
    """Jedes annotierte Feld der Klasse als Name und Typangabe."""
    for node in klasse.body:
        match node:
            case ast.AnnAssign(target=ast.Name(id=name), annotation=ast.expr() as annotation):
                yield name, annotation


def _names_a_primitive(annotation: ast.expr) -> bool:
    """Nennt die Typangabe irgendwo einen Rohwert-Typ.

    Auch verschachtelt: `Final[str]`, `str | None` und `tuple[str, ...]` halten
    genauso einen fest wie die nackte Angabe.
    """
    return any(_is_primitive(node) for node in ast.walk(annotation))


def _is_primitive(node: ast.AST) -> bool:
    """Erfasst `str` und `contexts.str`-artige Schreibweisen gleichermassen."""
    match node:
        case ast.Name(id=name) | ast.Attribute(attr=name) if name in _PRIMITIVES:
            return True
        case _:
            return False


def _denies_foreign_keys(klasse: ast.ClassDef) -> bool:
    """Sage, ob im Rumpf der Klasse `deny_foreign_key` aufgerufen wird."""
    return any(_is_guard_call(node) for node in ast.walk(klasse))


def _is_guard_call(node: ast.AST) -> bool:
    """Erfasst den Aufruf der Sperre, direkt wie ueber ein Modul-Praefix."""
    match node:
        case ast.Call(
            func=ast.Name(id="deny_foreign_key") | ast.Attribute(attr="deny_foreign_key")
        ):
            return True
        case _:
            return False


def _unguarded_raw_values(tree: ast.Module) -> Iterator[tuple[int, str]]:
    """Jede Klasse, die einen Rohwert haelt, ohne die Sperre vollstaendig zu ziehen."""
    for klasse in _classes(tree):
        fields = list(_fields(klasse))
        if not any(name != "key" and _names_a_primitive(a) for name, a in fields):
            continue

        if not any(name == "key" for name, _ in fields):
            yield klasse.lineno, f"{klasse.name} haelt einen Rohwert, aber kein `key`-Feld"

        elif not _denies_foreign_keys(klasse):
            yield klasse.lineno, f"{klasse.name} traegt `key`, ruft aber kein `deny_foreign_key`"


def test_jeder_rohwert_traegt_die_konstruktor_sperre() -> None:
    no_findings(
        (
            Befund(py_file, line, reason)
            for py_file, tree in modules(lambda path: _VALUE_OBJECT_DIR in path.parts)
            for line, reason in _unguarded_raw_values(tree)
        ),
        "Architektur-Verletzung: Rohwert ohne ConstructionKey gefunden:",
    )


def test_die_pruefung_schlaegt_ueberhaupt_an() -> None:
    """Ohne diesen Beleg waere ein gruener Ausgang auch dann gruen, wenn nichts geprueft wird."""
    luecke = ast.parse("@dataclass\nclass Offen:\n    value: Final[str]\n")

    assert list(_unguarded_raw_values(luecke)) == [
        (2, "Offen haelt einen Rohwert, aber kein `key`-Feld")
    ]
