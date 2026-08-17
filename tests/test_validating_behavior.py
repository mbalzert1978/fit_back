"""Das Validierungs-Behavior: es kuerzt ab und hebt die Feldfehler in den Fehlerkanal.

Eigene Datei neben `tests/test_pipeline.py`, weil es eine eigene Einheit ist:
dort geht es um die Naht (Reihenfolge, Abkuerzen), hier um das eine konkrete
Behavior, das an ihr und an `validation.py` haengt.
"""

import pytest

from src.contexts.shared_kernel.behaviors import validating
from src.contexts.shared_kernel.pipeline import Handler, build_pipeline
from src.contexts.shared_kernel.result import Err, Ok, Result
from src.contexts.shared_kernel.validation import FieldError, as_async

pytestmark = pytest.mark.asyncio


def _handler(protokoll: list[str]) -> Handler[str, str, str]:
    """Der innerste Schritt - er traegt sich ein und liefert `Ok`."""

    async def handle(request: str) -> Result[str, str]:
        protokoll.append("handler")
        return Ok(request)

    return handle


def _zu_kurz(request: str) -> list[FieldError]:
    """Eine Beispielregel - der Wert muss laenger als drei Zeichen sein."""
    kurz = 3
    if len(request) > kurz:
        return []
    return [FieldError("wert", "zu-kurz", {"minimum": kurz})]


async def test_die_validierung_kuerzt_ab_und_hebt_die_feldfehler_in_den_fehlerkanal() -> None:
    protokoll: list[str] = []

    kette = build_pipeline(
        _handler(protokoll),
        validating(as_async(_zu_kurz), lambda errors: f"ungueltig:{len(errors)}"),
    )
    ergebnis = await kette("ab")

    assert ergebnis == Err("ungueltig:1")
    assert protokoll == []


async def test_die_validierung_laesst_eine_gueltige_anfrage_durch() -> None:
    protokoll: list[str] = []

    kette = build_pipeline(
        _handler(protokoll),
        validating(as_async(_zu_kurz), lambda errors: f"ungueltig:{len(errors)}"),
    )
    ergebnis = await kette("lang genug")

    assert ergebnis == Ok("lang genug")
    assert protokoll == ["handler"]
