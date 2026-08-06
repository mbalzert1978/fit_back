"""Value Object UserTimeZone - IANA-Zeitzone, gegen die stdlib-Datenbank geprueft."""

from dataclasses import dataclass
from functools import cache
from typing import final
from zoneinfo import available_timezones

from src.shared_kernel import Err, Ok, Result

__all__ = ["DEFAULT_TIME_ZONE_ID", "UserTimeZone"]

DEFAULT_TIME_ZONE_ID = "Europe/Berlin"
"""Default laut BACKEND.md Abschnitt 1."""


@cache
def _known_time_zone_ids() -> frozenset[str]:
    """Lies die IANA-Kennungen einmal ein - `available_timezones` scannt jedes Mal neu."""
    return frozenset(available_timezones())


@final
@dataclass(frozen=True, slots=True)
class UserTimeZone:
    """Bekannte IANA-Zeitzonen-Id, in der die Tagebuch-Tage des Users liegen."""

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[UserTimeZone, str]:
        """Pruefe eine moeglicherweise unbekannte Zeitzonen-Id gegen die IANA-Datenbank."""
        trimmed = raw.strip()
        if trimmed not in _known_time_zone_ids():
            return Err(f"unbekannte Zeitzone: {raw!r}")
        return Ok(cls(trimmed))

    @classmethod
    def hydrate(cls, raw: str) -> UserTimeZone:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=time_zone):
                return time_zone
            case Err():
                raise AssertionError(f"unreachable: {raw!r} wurde vorgelagert validiert")
