"""Contract-Spec fuer das Ereignis `UserRegistered` (02-test-pyramide.md, Form B).

Der **Anbieter** pflegt kanonische Beispiel-Nutzlasten und belegt hier, dass das
tatsaechlich emittierte Ereignis genau einer davon entspricht - Feldmenge
**identisch**, nicht nur Teilmenge. Ein zusaetzliches Feld faellt damit ebenso
auf wie ein fehlendes, und beides faellt *hier* auf statt beim Konsumenten.

**Bei einer Abweichung ist die Beispiel-Datei massgeblich.** Sie ist der
veroeffentlichte Vertrag; der Produktionscode zieht nach, nicht umgekehrt. Ein
Feld darf additiv dazukommen (neue Datei mit erhoehter `<version>`); Umbenennen
oder Entfernen ist ein Bruch und braucht ein eigenes Ticket, das die Konsumenten
mitzieht.

Kein Netzwerk, keine Datenbank, kein Container: das Ereignis entsteht ueber die
Test-API des Slice, also auf demselben Weg wie in der Produktion. Wer die Naht
umginge und `user_registered(user)` direkt riefe, prueefte einen Vertrag, den der
laufende Code nie nimmt.
"""

import json
import pathlib
from collections.abc import Mapping

import pytest

from src.contexts.identity.application.register_user import (
    RegisterUserRequest,
    RegistrationAccepted,
    RegisterUserTestApi,
)
from src.contexts.identity.contracts import UserRegistered

BEISPIELE = (
    pathlib.Path(__file__).resolve().parents[2] / "contracts/events/user_registered/examples"
)

# Die Werte des kanonischen Beispiels - der Spec fuettert den Slice damit, statt
# eigene zu erfinden: nur dann ist "entspricht dem Beispiel" eine Aussage ueber
# den Aufbau und nicht ueber die Testdaten.
EMAIL = "markus@example.de"
LOCALE = "de"
ZEITZONE = "Europe/Berlin"
ZEITPUNKT = 1798221600

# Die Identitaet entsteht in `UserId.generate()` und kann deshalb nicht dieselbe
# sein wie im Beispiel. Verglichen wird sie ueber die Response des Use Case.
ERZEUGT = "userId"


def _beispiele() -> dict[str, Mapping[str, object]]:
    """Lies jede Beispiel-Nutzlast; der Dateiname bleibt als Fundstelle erhalten."""
    return {
        datei.name: json.loads(datei.read_text(encoding="utf-8"))
        for datei in sorted(BEISPIELE.glob("*.json"))
    }


def _beispiel_zur_nutzlast(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Loese das Beispiel ueber die **Feldmenge** auf, nie ueber seinen Dateinamen.

    Additiv kommt eine neue Datei mit erhoehter `<version>` dazu, die alte bleibt
    liegen (README daneben). Ein fest verdrahteter Dateiname pruefte danach die
    Werte des falschen Beispiels, waehrend die Produktion laengst das neue
    emittiert - der Test bliebe gruen und sagte nichts mehr.
    """
    felder = set(payload)
    passend = {name: b for name, b in _beispiele().items() if set(b) == felder}
    assert len(passend) == 1, (
        f"Die Nutzlast {sorted(payload)} passt auf {sorted(passend)} statt auf genau ein Beispiel. "
        f"Massgeblich ist die Datei unter {BEISPIELE}, nicht der Produktionscode."
    )
    return next(iter(passend.values()))


def test_es_gibt_ueberhaupt_ein_beispiel() -> None:
    """Ohne Beispiel-Datei prueft der Roundtrip-Spec unten nichts und bliebe trotzdem gruen."""
    assert _beispiele(), f"Keine Beispiel-Nutzlast unter {BEISPIELE}"


@pytest.mark.parametrize("name", sorted(_beispiele()))
def test_jedes_beispiel_traegt_die_felder_der_konsumenten(name: str) -> None:
    """Goals braucht Identitaet und Sprache, Diary zusaetzlich die Zeitzone."""
    assert set(_beispiele()[name]) >= {"userId", "email", "locale", "timeZoneId", "registeredAt"}


@pytest.mark.asyncio
async def test_das_emittierte_ereignis_entspricht_genau_einem_beispiel() -> None:
    """Feldmenge identisch - kein Feld zuviel, keines zu wenig.

    Das Aufloesen **ist** hier die Pruefung: `_beispiel_zur_nutzlast` verlangt
    genau ein Beispiel mit dieser Feldmenge und liefert dessen Inhalt.
    """
    api = RegisterUserTestApi().at_unix_time(ZEITPUNKT)

    ergebnis = await api.run(
        RegisterUserRequest(
            email=EMAIL,
            password="ein-langes-passwort",
            display_name="Markus",
            locale=LOCALE,
            time_zone_id=ZEITZONE,
        )
    )

    assert isinstance(ergebnis, RegistrationAccepted)
    (gemeldet,) = api.published_events
    assert gemeldet.event_type == UserRegistered.EVENT_TYPE
    assert _beispiel_zur_nutzlast(gemeldet.payload)


@pytest.mark.asyncio
async def test_das_emittierte_ereignis_traegt_die_werte_des_beispiels() -> None:
    """Gleiche Eingabe, gleiche Nutzlast - bis auf die erzeugte Identitaet."""
    api = RegisterUserTestApi().at_unix_time(ZEITPUNKT)

    ergebnis = await api.run(
        RegisterUserRequest(
            email=EMAIL,
            password="ein-langes-passwort",
            display_name="Markus",
            locale=LOCALE,
            time_zone_id=ZEITZONE,
        )
    )

    assert isinstance(ergebnis, RegistrationAccepted)
    (gemeldet,) = api.published_events
    beispiel = _beispiel_zur_nutzlast(gemeldet.payload)
    assert gemeldet.payload[ERZEUGT] == ergebnis.user_id
    assert {feld: wert for feld, wert in gemeldet.payload.items() if feld != ERZEUGT} == {
        feld: wert for feld, wert in beispiel.items() if feld != ERZEUGT
    }
