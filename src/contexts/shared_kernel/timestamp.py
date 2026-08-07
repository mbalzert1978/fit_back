"""Zeitpunkt als Unix-Sekunden-Value-Object.

Verbindlich seit `docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md`:
ein Zeitpunkt ist ueberall in Domaene und Persistenz ein `int` Unix-Sekunden,
gewrappt in dieses Value Object - nie ein rohes `datetime`
(.rules/python/python-data-access.md, "Zeitpunkte als Unix-Sekunden-Value-Object").

Der Grund ist Speichernaehe: ein `int` verhaelt sich in jeder Engine gleich -
PostgreSQL `bigint`, SQLite `INTEGER` - und kennt weder Zeitzonen- noch
Serialisierungs-Mehrdeutigkeit. Die Umrechnung nach `datetime` passiert nur am
Rand, wenn eine Anzeige oder ein ISO-8601-Transportwert noetig ist.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import final

__all__ = ["Timestamp"]


@final
@dataclass(frozen=True, slots=True)
class Timestamp:
    """Ein Zeitpunkt in ganzen Sekunden seit dem Unix-Epoch (UTC)."""

    unix_seconds: int

    @classmethod
    def from_datetime(cls, moment: datetime) -> Timestamp:
        """Rechne einen tz-bewussten `datetime` in Unix-Sekunden um.

        Ein naiver `datetime` ist ein Programmierfehler, kein Fachfall - der
        Aufrufer haette nie einen ohne Zeitzone haben duerfen.
        """
        if moment.tzinfo is None:
            msg = "Timestamp.from_datetime erfordert einen tz-bewussten datetime"
            raise ValueError(msg)
        return cls(int(moment.timestamp()))

    def to_datetime(self) -> datetime:
        """Rechne zurueck nach UTC - nur am Rand (Anzeige, ISO-8601-Transport)."""
        return datetime.fromtimestamp(self.unix_seconds, UTC)
