"""TimeProvider-Protocol für deterministisch testbare Zeitmessung."""

from datetime import UTC, datetime
from typing import Protocol, final

from src.contexts.shared_kernel.timestamp import Timestamp


class TimeProvider(Protocol):
    """Port: Liefert die aktuelle Zeit.

    Zwei Zugriffe, bewusst mit verschiedenen Adressaten:

    - `now()` ist der **domaenenseitige** Weg und liefert ein `Timestamp`
      (Unix-Sekunden). Alles, was einen Zeitpunkt fachlich festhaelt, nimmt diesen.
    - `utc_now()` ist die rohe Systemablesung als tz-bewusster `datetime` und
      gehoert an den Rand - dorthin, wo tatsaechlich ein `datetime` gebraucht wird
      (Transport-Formatierung, Bibliotheken, die nichts anderes akzeptieren).
    """

    def now(self) -> Timestamp:
        """Liefere die aktuelle Zeit als Unix-Sekunden-Value-Object."""
        ...

    def utc_now(self) -> datetime:
        """Liefere die aktuelle Zeit in UTC als tz-aware datetime."""
        ...


@final
class SystemTimeProvider:
    """Standard-Implementierung: liefert die echte aktuelle System-Zeit."""

    def now(self) -> Timestamp:
        """Liefere die aktuelle Zeit als Unix-Sekunden-Value-Object."""
        return Timestamp.from_datetime(self.utc_now())

    def utc_now(self) -> datetime:
        """Liefere die aktuelle Zeit in UTC."""
        return datetime.now(UTC)


@final
class FakeTimeProvider:
    """Test-Implementierung: Zeit ist setzbar für deterministische Tests."""

    def __init__(self, fixed_time: datetime | None = None) -> None:
        """Initialisiere mit optionaler fester Zeit (standard: UTC 2000-01-01 00:00:00)."""
        if fixed_time is None:
            fixed_time = datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC)
        elif fixed_time.tzinfo is None:
            raise ValueError("FakeTimeProvider erfordert tz-aware datetime")
        self._time = fixed_time

    def now(self) -> Timestamp:
        """Liefere die vorgegebene Zeit als Unix-Sekunden-Value-Object."""
        return Timestamp.from_datetime(self._time)

    def utc_now(self) -> datetime:
        """Liefere die vorgegebene oder setzte Zeit."""
        return self._time

    def set_time(self, new_time: datetime) -> None:
        """Setze eine neue Zeit (muss tz-aware sein)."""
        if new_time.tzinfo is None:
            raise ValueError("set_time erfordert tz-aware datetime")
        self._time = new_time
