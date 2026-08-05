"""Architektur-Test: kein direkter datetime.utcnow() oder datetime.now() ohne Timezone."""

import ast
from pathlib import Path


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
            with open(py_file) as f:
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
