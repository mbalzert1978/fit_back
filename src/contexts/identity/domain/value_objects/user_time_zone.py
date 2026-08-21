"""Value Object UserTimeZone - IANA-Zone oder fester UTC-Versatz."""

import re
from dataclasses import dataclass
from functools import cache
from typing import final
from zoneinfo import available_timezones

from src.contexts.identity.domain.user_time_zone_errors import (
    UserTimeZoneError,
    UserTimeZoneUnknown,
)
from src.contexts.shared_kernel import Err, Ok, Result

__all__ = ["DEFAULT_TIME_ZONE_ID", "UserTimeZone"]

DEFAULT_TIME_ZONE_ID = "Europe/Berlin"
"""Default laut BACKEND.md Abschnitt 1."""

_OFFSET = re.compile(r"^(?:UTC|GMT)?(?P<sign>[+-])(?P<hours>\d{1,2}):?(?P<minutes>\d{2})$")
"""Ein fester Versatz gegen UTC, in den Schreibweisen, die der Vertrag schickt.

`GMT+01:00` kommt aus einer der beiden 201-Interaktionen des Frontend-Vertrags
und ist **keine** IANA-Zone - gemessen gegen `zoneinfo.available_timezones()`.
Der Vertrag gewinnt, die Invariante wird nachgezogen
(`docs/decisions/2026-08-21-2200-vertrag-zieht-anzeigename-und-zeitzone-nach.md`).

Das Praefix ist optional, weil `+01:00` und `GMT+01:00` dieselbe Zone meinen;
der Doppelpunkt ist es, weil `+0100` dieselbe ISO-8601-Schreibweise ist.
"""

_MAXIMUM_HOURS = 23
_MAXIMUM_MINUTES = 59


@cache
def _known_time_zone_ids() -> frozenset[str]:
    """Lies die IANA-Kennungen einmal ein - `available_timezones` scannt jedes Mal neu."""
    return frozenset(available_timezones())


def _normalized_offset(raw: str) -> str | None:
    """Bringe einen festen Versatz auf die eine Form `±HH:MM`, sonst None.

    Genau eine Schreibweise geht in den Bestand: sonst waeren `GMT+01:00`,
    `+0100` und `+01:00` drei Werte fuer dieselbe Zone, und jeder Vergleich
    darauf muesste sie erst wieder zusammenfuehren.
    """
    if (found := _OFFSET.match(raw)) is None:
        return None
    hours, minutes = int(found["hours"]), int(found["minutes"])
    if hours > _MAXIMUM_HOURS or minutes > _MAXIMUM_MINUTES:
        return None
    return f"{found['sign']}{hours:02d}:{minutes:02d}"


@final
@dataclass(frozen=True, slots=True)
class UserTimeZone:
    """Die Zone, in der die Tagebuch-Tage des Users liegen.

    Zwei Formen, und nur diese zwei: eine bekannte IANA-Kennung
    (`Europe/Berlin`) oder ein fester Versatz gegen UTC (`+01:00`). Wer den Wert
    in eine `tzinfo` verwandelt, muss beide behandeln - `ZoneInfo` kennt den
    Versatz nicht, `datetime.timezone` kennt die Sommerzeit nicht.
    """

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[UserTimeZone, UserTimeZoneError]:
        """Pruefe eine Zeitzonen-Angabe gegen die IANA-Datenbank oder als festen Versatz.

        Die IANA-Datenbank zuerst: `Etc/GMT-1` ist eine Kennung und kein
        Versatz, und sie soll auch als Kennung stehenbleiben.
        """
        trimmed = raw.strip()
        if trimmed in _known_time_zone_ids():
            return Ok(cls(trimmed))
        if (offset := _normalized_offset(trimmed)) is not None:
            return Ok(cls(offset))
        return Err(UserTimeZoneUnknown(raw))

    @classmethod
    def hydrate(cls, raw: str) -> UserTimeZone:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=time_zone):
                return time_zone
            case Err():
                msg = f"unreachable: {raw!r} wurde vorgelagert validiert"
                raise AssertionError(msg)
