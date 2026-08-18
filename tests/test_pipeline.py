"""Die beiden Zusagen der Pipeline: Reihenfolge und Abkuerzen.

Beides ist nicht an der Signatur abzulesen und beides traegt den Rest: haengt
spaeter eine Transaktionsklammer oder eine Idempotenz-Pruefung als Behavior in
der Kette, entscheidet genau das, ob sie wirkt.
"""

import pytest

from src.contexts.shared_kernel.pipeline import Behavior, Handler, build_pipeline
from src.contexts.shared_kernel.result import Err, Ok, Result
from src.contexts.shared_kernel.validation import AsyncRule, FieldError, all_of_async

pytestmark = pytest.mark.asyncio


def _handler(protokoll: list[str]) -> Handler[str, str, str]:
    """Der innerste Schritt - er traegt sich ein und liefert `Ok`."""

    async def handle(request: str) -> Result[str, str]:
        protokoll.append("handler")
        return Ok(request)

    return handle


def _durchreichend(name: str, protokoll: list[str]) -> Behavior[str, str, str]:
    """Ein Behavior, das sich vor und nach dem naechsten Schritt eintraegt."""

    async def behave(request: str, inner: Handler[str, str, str]) -> Result[str, str]:
        protokoll.append(f"{name}-vorher")
        ergebnis = await inner(request)
        protokoll.append(f"{name}-nachher")
        return ergebnis

    return behave


def _abkuerzend(name: str, protokoll: list[str]) -> Behavior[str, str, str]:
    """Ein Behavior, das `Err` liefert, ohne den naechsten Schritt zu rufen."""

    async def behave(_: str, __: Handler[str, str, str]) -> Result[str, str]:
        protokoll.append(name)
        return Err(name)

    return behave


async def test_ohne_behavior_laeuft_der_handler_unveraendert() -> None:
    protokoll: list[str] = []

    ergebnis = await build_pipeline(_handler(protokoll))("anfrage")

    assert ergebnis == Ok("anfrage")
    assert protokoll == ["handler"]


async def test_das_erste_behavior_liegt_aussen() -> None:
    """`build_pipeline(h, a, b)` laeuft a -> b -> h und danach zurueck."""
    protokoll: list[str] = []

    kette = build_pipeline(
        _handler(protokoll), _durchreichend("a", protokoll), _durchreichend("b", protokoll)
    )
    await kette("anfrage")

    assert protokoll == ["a-vorher", "b-vorher", "handler", "b-nachher", "a-nachher"]


async def test_ein_behavior_mit_err_laesst_den_handler_nicht_laufen() -> None:
    """Die eine Zusage, ohne die eine Kette nur eine Aufrufliste waere."""
    protokoll: list[str] = []

    kette = build_pipeline(_handler(protokoll), _abkuerzend("stopp", protokoll))
    ergebnis = await kette("anfrage")

    assert ergebnis == Err("stopp")
    assert protokoll == ["stopp"]


async def test_ein_abkuerzendes_behavior_stoppt_auch_die_folgenden() -> None:
    protokoll: list[str] = []

    kette = build_pipeline(
        _handler(protokoll), _abkuerzend("stopp", protokoll), _durchreichend("danach", protokoll)
    )
    ergebnis = await kette("anfrage")

    assert ergebnis == Err("stopp")
    assert protokoll == ["stopp"]


async def test_all_of_async_sammelt_alle_befunde_in_regelreihenfolge() -> None:
    """Collect-all bleibt collect-all, auch wenn die Regeln warten muessen."""

    def regel(feld: str) -> AsyncRule[str]:
        async def pruefe(_: str) -> list[FieldError]:
            return [FieldError(feld, "fehlt", {})]

        return pruefe

    kombiniert = all_of_async(regel("a"), regel("b"), regel("c"))

    assert [error.field for error in await kombiniert("egal")] == ["a", "b", "c"]
