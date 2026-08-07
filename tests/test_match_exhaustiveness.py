"""Jeder `match` in `src/` ist vollstaendig.

Python erzwingt Vollzaehligkeit zur Laufzeit nicht: passt kein Zweig, faellt der
`match` still durch und die Funktion liefert `None`. Der Fehler schlaegt dann
weit weg von seiner Ursache als `AttributeError` auf einem `NoneType` auf. Ein
Typpruefer wuerde das melden - dieses Repo faehrt bewusst ohne einen, also
uebernimmt dieser Test die Aufgabe.

Geprueft wird der **letzte** Zweig: er wirft (`raise`) oder ruft `assert_never`.
Beides beendet den `match` laut. Ein aufgezaehlter `match`, der einfach aufhoert,
faellt hier durch.

Die Ausnahmen stehen in `OFFENE_WERTEMENGEN` - Stellen, an denen der Restfall
**real** ist, weil die Fallmenge einer fremden Bibliothek gehoert und nicht uns.
Dort waere `assert_never` schaedlich: ein Bibliotheks-Update brachte den Aufrufer
um seine Antwort. Ein neuer Eintrag kostet eine Begruendung und ist damit eine
Entscheidung, kein Versehen.

Regel: `.rules/python/python-error-handling.md`, "Jeder `match` ist vollstaendig".
"""

import ast
import pathlib

import pytest

QUELLE = pathlib.Path(__file__).resolve().parents[1] / "src"

OFFENE_WERTEMENGEN = {
    "api/exception_handlers.py": (
        "matcht auf Pydantics Fehlertyp-String, nicht auf eine Union dieses Repos. "
        "Ein neuer Pydantic-Fehlertyp ist ein Bibliotheks-Update, kein Programmierfehler - "
        "`assert_never` machte daraus einen 500er statt einer uebersetzten 400."
    ),
}
"""Dateien, deren `match` bewusst auf eine offene Wertemenge trifft, mit Begruendung."""


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
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Match) and not _endet_laut(knoten.cases[-1]):
                offen.append((relativ, knoten.lineno))
    return offen


def test_jeder_match_endet_laut() -> None:
    """Kein `match` darf still durchfallen und `None` liefern."""
    unerlaubt = [
        f"src/{datei}:{zeile}"
        for datei, zeile in _offene_match_stellen()
        if datei not in OFFENE_WERTEMENGEN
    ]

    assert not unerlaubt, (
        "Diese `match`-Stellen enden ohne werfenden Zweig und liefern bei einem "
        "unbekannten Fall still `None`:\n  - " + "\n  - ".join(unerlaubt) + "\n\n"
        "Gehoert die Fallmenge diesem Repo, gehoert ans Ende `case _: assert_never(<subjekt>)`. "
        "Gehoert sie einer fremden Bibliothek, gehoert die Datei mit Begruendung in "
        "OFFENE_WERTEMENGEN in dieser Datei."
    )


@pytest.mark.parametrize("datei", sorted(OFFENE_WERTEMENGEN))
def test_jede_ausnahme_wird_noch_gebraucht(datei: str) -> None:
    """Eine Ausnahme, die niemand mehr braucht, gehoert geloescht statt vererbt."""
    assert any(offen == datei for offen, _ in _offene_match_stellen()), (
        f"{datei} steht in OFFENE_WERTEMENGEN, hat aber keinen offenen `match` mehr. "
        "Der Eintrag ist veraltet und gehoert entfernt - sonst deckt er kuenftig "
        "eine echte Luecke zu."
    )
