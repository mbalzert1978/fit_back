"""Startup-Prüfung — Pydantic-Fehlertypen-Kompatibilität beim Start verifizieren.

`_fault_of` in [`exception_handlers.py`](./exception_handlers.py) bildet Pydantics
Fehlertyp-Strings auf eigene Faelle ab und schliesst mit `assert_never` - ein unbekannter
Typ ist dort ein Bruch, keine Kleinigkeit, denn er wuerde dem Aufrufer sonst still eine
falsche Begruendung nennen.

Ohne diese Pruefung traefe der Bruch aber zuerst einen Nutzer: die Anfrage liefe in den
`AssertionError` und der Aufrufer bekaeme HTTP 500 statt seiner uebersetzten 400. Deshalb
wird die Annahme beim Start geprueft, wo ein Fehlschlag das Deployment stoppt statt eine
Anfrage.

Was hier auffaellt, ist der Fall, der uns tatsaechlich bricht: ein Fehlertyp, den wir
behandeln, ist im installierten Pydantic **verschwunden oder umbenannt**. Was hier nicht
auffaellt, sind neu **hinzugekommene** Typen - ob unser Schema sie ueberhaupt erzeugen
kann, sagt diese Liste nicht. Diese Haelfte deckt der Vertragstest ab, der das Modell
gegen jede Form kaputter Eingabe faehrt (`tests/api/test_pydantic_error_contract.py`).
Zusammen decken beide den Weg ab: die CI meldet, was sich am Verhalten aendert, der
Start meldet, was gar nicht mehr existiert.

Entscheidung: docs/decisions/2026-08-07-1120-jeder-match-endet-mit-assert-never.md
"""

from typing import get_args

from pydantic_core import ErrorType

from src.api.exception_handlers import HANDLED_PYDANTIC_ERROR_TYPES

__all__ = ["verify_pydantic_contract"]


def verify_pydantic_contract() -> None:
    """Pruefe, dass jeder behandelte Fehlertyp im installierten Pydantic noch existiert.

    Raises:
        ValueError: wenn ein behandelter Typ fehlt - mit allen fehlenden auf einmal.

    """
    bekannt = set(get_args(ErrorType))
    if verschwunden := sorted(HANDLED_PYDANTIC_ERROR_TYPES - bekannt):
        msg = (
            f"Das installierte Pydantic kennt diese Fehlertypen nicht mehr: {verschwunden}. "
            "`_fault_of` in src/api/exception_handlers.py behandelt sie - entweder wurden sie "
            "umbenannt (dann dort und in HANDLED_PYDANTIC_ERROR_TYPES nachziehen) oder "
            "entfernt (dann den Fall streichen). Bis dahin startet die Anwendung nicht, "
            "damit der Bruch nicht erst einen Nutzer trifft."
        )
        raise ValueError(msg)
