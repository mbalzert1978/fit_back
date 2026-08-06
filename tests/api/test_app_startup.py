"""Smoke-Test des Anwendungs-Einstiegspunkts.

Klein, aber die Luecke, die er schliesst, war teuer: `main.py` liess sich ueber
mehrere Tickets hinweg **nicht importieren** - zwei Importe zeigten auf Module,
die es nicht gibt (`fastapi.middleware.base`, `starlette.middleware.csrf`). Sie
kamen aus einem Commit, der zurueckgenommen wurde, und ueber den Merge eines
aelteren Branches unbemerkt zurueck. Die CI blieb gruen, weil kein einziger Test
das Modul je geladen hat.

Deshalb hier keine Fachlichkeit, sondern nur: das Modul laedt, und die
Anwendung kennt ihre Endpunkte.
"""

import pytest


def test_der_einstiegspunkt_laesst_sich_importieren() -> None:
    """`import main` darf keine Umgebungsvariablen und keine Datenbank brauchen.

    Die Konfiguration wird erst beim Start geprueft (`lifespan`), nicht beim
    Import - sonst waere jedes Werkzeug, das das Modul nur laden will, an eine
    vollstaendige Umgebung gebunden.
    """
    import main

    assert main.app.title == "Fit-back API"


@pytest.mark.parametrize("path", ["/api/v1/health", "/api/v1/identity/register"])
def test_die_anwendung_kennt_ihre_endpunkte(path: str) -> None:
    """Gegen das OpenAPI-Schema geprueft, nicht gegen `app.routes`.

    FastAPI haengt eingebundene Router als Referenz ein, statt ihre Routen
    flachzuziehen; das Schema ist die verlaessliche Aufzaehlung.
    """
    import main

    assert path in main.app.openapi()["paths"]
