"""Die Startup-Pruefung des Pydantic-Vertrags schlaegt an, wenn ein Typ verschwindet.

`verify_pydantic_contract` soll das Deployment stoppen, bevor ein Aufrufer den Bruch
sieht. Ein Waechter, von dem niemand belegt hat, dass er ausloest, ist keiner - deshalb
wird hier beides geprueft: er laesst den echten Stand durch, und er schlaegt an, wenn
ein behandelter Fehlertyp im installierten Pydantic fehlt.

Regel: `.rules/python/python-error-handling.md`, "Jeder `match` ist vollstaendig".
"""

import pytest

from src.api import pydantic_contract_check
from src.api.exception_handlers import HANDLED_PYDANTIC_ERROR_TYPES
from src.api.pydantic_contract_check import verify_pydantic_contract


def test_der_echte_stand_geht_durch() -> None:
    verify_pydantic_contract()


def test_ein_verschwundener_fehlertyp_stoppt_den_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pydantic_contract_check,
        "HANDLED_PYDANTIC_ERROR_TYPES",
        HANDLED_PYDANTIC_ERROR_TYPES | {"diesen_typ_gibt_es_nicht"},
    )

    with pytest.raises(ValueError, match="diesen_typ_gibt_es_nicht") as scheitern:
        verify_pydantic_contract()

    assert "exception_handlers" in str(scheitern.value), (
        "Die Meldung muss sagen, wo der Fall behandelt wird - sonst sucht der Leser."
    )
