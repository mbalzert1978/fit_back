"""Architektur-Tests rund um Zeit: kein ungebundenes Ablesen, kein `datetime` in der Domaene.

Zwei verschiedene Regeln, die leicht verwechselt werden:

1. **Woher** kommt die Zeit? Nie aus `datetime.now()`/`utcnow()` direkt, sondern
   aus dem `TimeProvider` - sonst ist kein Ablauf deterministisch testbar.
2. **Was** haelt die Domaene? Einen `Timestamp` (Unix-Sekunden), nie einen
   `datetime`. Ein `datetime` traegt Zeitzone, Kalender und Aufloesung mit sich
   herum - lauter Entscheidungen, die an den Rand gehoeren
   (`docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md`).

Der erste Test faengt Regel 1 - Aufrufe. Der zweite faengt Regel 2 - Typen, die
in Feldern, Parametern und Rueckgaben stehen. Sie ueberschneiden sich nicht:
ein Aggregat, das einen von aussen gereichten `datetime` nur *haelt*, ruft
nirgends `datetime.now()` auf und war fuer den ersten Test unsichtbar.
"""

import ast
from pathlib import Path

# Die Schichten, in denen Zeit ausschliesslich als `Timestamp` gefuehrt wird.
# `application` und `api` fehlen bewusst: Response-DTO und Router sind die
# Uebersetzung an den Rand hin, und ISO-8601 auf der Leitung braucht dort
# irgendwann einen `datetime`.
_TIMESTAMP_ONLY_LAYERS = ("domain", "contracts")


def test_no_direct_datetime_calls_without_timezone() -> None:
    """
    Stelle sicher, dass kein Modul unter src/ direkt datetime.utcnow() oder
    datetime.now() ohne Timezone aufruft (ausserhalb der TimeProvider-Implementierung).

    Diese Regel wird durchgesetzt durch statische Code-Analyse: Durchsuche alle
    Python-Dateien unter src/ nach den verbotenen Patterns.
    """
    src_root = Path(__file__).parent.parent / "src"
    errors: list[tuple[Path, int, str]] = []

    # Dateien, die NICHT überprüft werden (TimeProvider selbst)
    exclude_patterns = [
        "shared_kernel/time_provider.py",
    ]

    for py_file in src_root.rglob("*.py"):
        # Überspringe ausgeschlossene Dateien
        relative_path = py_file.relative_to(src_root)
        if any(relative_path.as_posix().endswith(pat) for pat in exclude_patterns):
            continue

        try:
            # encoding explizit: ohne sie liest Windows in cp1252 und bricht an
            # jedem Nicht-Latin-1-Zeichen im Quelltext ab (z. B. den IDN-Beispielen
            # in identity/domain/value_objects/email.py).
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            # Parse den AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                errors.append((py_file, e.lineno or 0, f"SyntaxError: {e}"))
                continue

            # Durchsuche nach Calls zu datetime.utcnow() oder datetime.now()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Überprüfe auf datetime.utcnow()
                    if (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "utcnow"
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "datetime"
                    ):
                        errors.append(
                            (
                                py_file,
                                node.lineno or 0,
                                "datetime.utcnow() ist verboten — nutze TimeProvider.utc_now() stattdessen",
                            )
                        )

                    # Überprüfe auf datetime.now() ohne tzinfo-Argument
                    if (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "now"
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "datetime"
                    ):
                        # Prüfe, ob tz oder tzinfo als Argument gesetzt ist
                        has_tzinfo = False
                        for keyword in node.keywords:
                            if keyword.arg in ("tz", "tzinfo"):
                                has_tzinfo = True
                                break
                        if not has_tzinfo:
                            errors.append(
                                (
                                    py_file,
                                    node.lineno or 0,
                                    "datetime.now() ohne tz-Argument ist verboten — nutze TimeProvider.utc_now() stattdessen",
                                )
                            )
        except Exception as e:  # noqa: BLE001 - Architektur-Scan darf an keiner Datei hart abbrechen
            errors.append((py_file, 0, f"Error beim Durchsuchen: {e}"))

    if errors:
        msg = "Architektur-Verletzung: datetime-Aufrufe ohne Timezone gefunden:\n"
        for file_path, line_no, error_msg in errors:
            msg += f"  {file_path}:{line_no}: {error_msg}\n"
        raise AssertionError(msg)


def _annotations(tree: ast.Module) -> list[tuple[int, ast.expr]]:
    """Sammle jede Typangabe des Moduls samt Zeilennummer.

    Drei Stellen, an denen ein Typ einen Wert festhaelt: annotierte Zuweisungen
    (Klassenfelder, Dataclass-Felder, Modulvariablen), Parameter samt allen
    Sonderformen (`*args`, `**kwargs`, keyword-only) und Rueckgabetypen.
    """
    found: list[tuple[int, ast.expr]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and node.annotation is not None:
            found.append((node.lineno, node.annotation))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.returns is not None:
                found.append((node.lineno, node.returns))
            args = node.args
            for argument in [
                *args.posonlyargs,
                *args.args,
                *args.kwonlyargs,
                args.vararg,
                args.kwarg,
            ]:
                if argument is not None and argument.annotation is not None:
                    found.append((argument.lineno, argument.annotation))
    return found


def _names_datetime(annotation: ast.expr) -> bool:
    """Nennt diese Typangabe irgendwo `datetime`?

    Auch verschachtelt, denn `datetime | None`, `list[datetime]` und
    `Mapping[str, datetime]` halten genauso einen `datetime` fest wie die nackte
    Angabe. `datetime.datetime` wird ueber das Attribut miterfasst.
    """
    return any(
        (isinstance(node, ast.Name) and node.id == "datetime")
        or (isinstance(node, ast.Attribute) and node.attr == "datetime")
        for node in ast.walk(annotation)
    )


def test_domaene_haelt_keinen_datetime() -> None:
    """Kein Feld, Parameter oder Rueckgabetyp unter `domain/` oder `contracts/` ist ein datetime.

    Der Test daneben prueft nur *Aufrufe* - ein Aggregat, das einen von aussen
    gereichten `datetime` bloss haelt, ruft nichts auf und rutschte bisher
    durch. Zeit wird in der Domaene als `Timestamp` gefuehrt; die Umrechnung in
    einen `datetime` ist Sache des Randes.
    """
    src_root = Path(__file__).parent.parent / "src"
    errors: list[str] = []

    for py_file in src_root.rglob("*.py"):
        parts = py_file.relative_to(src_root).parts
        if not any(layer in parts for layer in _TIMESTAMP_ONLY_LAYERS):
            continue

        # encoding explizit, siehe Begruendung im Test darueber.
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for line_no, annotation in _annotations(tree):
            if _names_datetime(annotation):
                errors.append(
                    f"  {py_file}:{line_no}: haelt einen datetime - "
                    f"nutze Timestamp (Unix-Sekunden) und wandle erst am Rand um"
                )

    if errors:
        raise AssertionError(
            "Architektur-Verletzung: datetime in der Domaene gefunden:\n" + "\n".join(errors)
        )
