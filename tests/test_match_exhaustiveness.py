"""Jeder `match` in `src/` ist vollstaendig.

Python erzwingt Vollzaehligkeit zur Laufzeit nicht: passt kein Zweig, faellt der
`match` still durch und die Funktion liefert `None`. Der Fehler schlaegt dann
weit weg von seiner Ursache als `AttributeError` auf einem `NoneType` auf.

Geprueft wird der **letzte** Zweig: er wirft (`raise`) oder ruft `assert_never`.
Beides beendet den `match` laut. Ein aufgezaehlter `match`, der einfach aufhoert,
faellt hier durch.

**Ohne Ausnahmen.** Das gilt auch dort, wo die Fallmenge einer fremden Bibliothek
gehoert - Pydantics Fehlertypen im Exception-Handler sind der Fall im Repo. Der
Einwand "ein Bibliotheks-Update ist kein Programmierfehler" traegt nicht: eine
Aenderung, die wir nicht adressiert haben, ist ebenso ein Bruch, und sie still
auf einen Auffangzweig abzubilden hiesse, dem Aufrufer eine falsche Begruendung
zu nennen. Damit der Bruch nicht erst bei einem Nutzer auftritt, wird die Annahme
frueher geprueft: `verify_pydantic_contract` beim Start und
`tests/api/test_pydantic_error_contract.py` in der CI.

Regel: `.rules/python/python-error-handling.md`, "Jeder `match` ist vollstaendig".
"""

import ast
import pathlib

QUELLE = pathlib.Path(__file__).resolve().parents[1] / "src"


def _endet_laut(zweig: ast.match_case) -> bool:
    """Wirft der Zweig, oder ruft er `assert_never`?"""
    for knoten in ast.walk(zweig):
        if isinstance(knoten, ast.Raise):
            return True
        if (
            isinstance(knoten, ast.Call)
            and isinstance(knoten.func, ast.Name)
            and knoten.func.id == "assert_never"
        ):
            return True
    return False


def _offene_match_stellen() -> list[tuple[str, int]]:
    """Alle `match`-Stellen in `src/`, deren letzter Zweig nicht laut endet."""
    offen = []
    for datei in sorted(QUELLE.rglob("*.py")):
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        relativ = datei.relative_to(QUELLE).as_posix()
        offen.extend(
            (relativ, knoten.lineno)
            for knoten in ast.walk(baum)
            if isinstance(knoten, ast.Match) and not _endet_laut(knoten.cases[-1])
        )
    return offen


def test_jeder_match_endet_laut() -> None:
    """Kein `match` darf still durchfallen und `None` liefern."""
    unerlaubt = [f"src/{datei}:{zeile}" for datei, zeile in _offene_match_stellen()]

    assert not unerlaubt, (
        "Diese `match`-Stellen enden ohne werfenden Zweig und liefern bei einem "
        "unbekannten Fall still `None`:\n  - " + "\n  - ".join(unerlaubt) + "\n\n"
        "Ans Ende gehoert `case _: assert_never(<subjekt>)`. Ist das Subjekt ein "
        "Ausdruck statt eines Namens, erst binden, dann matchen. Gehoert die Fallmenge "
        "einer fremden Bibliothek, aendert das nichts an dieser Regel - dann kommt eine "
        "Startup-Pruefung dazu, die den Bruch vor die erste Anfrage zieht (Vorbild: "
        "src/api/pydantic_contract_check.py)."
    )
