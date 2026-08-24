"""Value Object `UserTimeZone` - IANA-Kennung oder fester UTC-Versatz.

Die gueltigen Formen sind die, die der Frontend-Vertrag schickt
(`contracts/pacts/identity/`): `Europe/Berlin` als Kennung, `GMT+01:00` als
Versatz, der auf `+01:00` normalisiert zurueckkommt.
"""

import pytest

from src.contexts.identity.domain.user_time_zone_errors import (
    UserTimeZoneIsEmpty,
    UserTimeZoneUnknown,
)
from src.contexts.identity.domain.value_objects.user_time_zone import UserTimeZone
from src.contexts.shared_kernel import Err, Ok


@pytest.mark.parametrize(
    ("raw", "erwartet"),
    [
        ("Europe/Berlin", "Europe/Berlin"),
        ("GMT+01:00", "+01:00"),
        ("Etc/GMT-1", "Etc/GMT-1"),
        ("+0100", "+01:00"),
        ("UTC+01:00", "+01:00"),
        ("  Europe/Berlin  ", "Europe/Berlin"),
    ],
)
def test_a_known_form_is_accepted_and_normalized(raw: str, erwartet: str) -> None:
    """Beleg: beide Formen gehen durch, der Versatz in genau einer Schreibweise."""
    assert UserTimeZone.parse(raw) == Ok(UserTimeZone(erwartet))


@pytest.mark.parametrize("raw", ["UTCGMT+01:00", "+25:00", "Europe/Nirgendwo", "GMTGMT+01:00"])
def test_anything_else_is_one_unknown_case(raw: str) -> None:
    """Beleg: ein doppeltes Praefix ist keine Zone, und `+25:00` auch nicht."""
    assert UserTimeZone.parse(raw) == Err(UserTimeZoneUnknown(raw))


@pytest.mark.parametrize("raw", ["", "   "])
def test_an_empty_value_is_its_own_case(raw: str) -> None:
    """Beleg: "gar nichts angegeben" bleibt vom Unbekannten getrennt."""
    assert UserTimeZone.parse(raw) == Err(UserTimeZoneIsEmpty())
