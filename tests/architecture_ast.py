"""Die gemeinsamen Bausteine der Architektur-Tests: Quelldateien lesen, Befunde melden.

Kein Test, sondern das, worauf `test_architecture_*.py` sich stuetzt. Ein
Architektur-Test besteht immer aus denselben drei Teilen: eine Auswahl von
Quelldateien, eine Suche im Syntaxbaum, eine Meldung aus allen Fundstellen. Der
mittlere Teil ist je Regel verschieden, die beiden aeusseren nicht.
"""

import ast
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final, final

__all__ = ["Befund", "modules", "no_findings"]

_SRC_ROOT: Final = Path(__file__).parent.parent / "src"


@final
@dataclass(frozen=True, slots=True)
class Befund:
    """Eine Fundstelle samt Grund, in der Form, in der sie in der Meldung steht."""

    file: Path
    line: int
    reason: str

    def __str__(self) -> str:
        return f"  {self.file}:{self.line}: {self.reason}"


def modules(keep: Callable[[Path], bool]) -> Iterator[tuple[Path, ast.Module]]:
    """Jede Quelldatei unter `src/`, die `keep` durchlaesst, als geparster Baum.

    `keep` bekommt den Pfad relativ zu `src/`. `encoding` explizit: ohne sie
    liest Windows in cp1252 und bricht an jedem Nicht-Latin-1-Zeichen ab
    (z. B. den IDN-Beispielen in `identity/domain/value_objects/email.py`).
    """
    for py_file in _SRC_ROOT.rglob("*.py"):
        if keep(py_file.relative_to(_SRC_ROOT)):
            yield py_file, ast.parse(py_file.read_text(encoding="utf-8"))


def no_findings(findings: Iterable[Befund], headline: str) -> None:
    """Lass alle Befunde als eine Meldung auflaufen, nicht nur den ersten."""
    if found := list(findings):
        raise AssertionError("\n".join([headline, *map(str, found)]))
