"""TimeProvider-Protocol für deterministisch testbare Zeitmessung."""

from datetime import datetime, timezone
from typing import Protocol


class TimeProvider(Protocol):
    """Port: Liefert die aktuelle Zeit als tz-aware datetime in UTC."""

    def utc_now(self) -> datetime:
        """Liefere die aktuelle Zeit in UTC als tz-aware datetime."""
        ...


class SystemTimeProvider:
    """Standard-Implementierung: liefert die echte aktuelle System-Zeit."""

    def utc_now(self) -> datetime:
        """Liefere die aktuelle Zeit in UTC."""
        return datetime.now(timezone.utc)


class FakeTimeProvider:
    """Test-Implementierung: Zeit ist setzbar für deterministische Tests."""

    def __init__(self, fixed_time: datetime | None = None) -> None:
        """Initialisiere mit optionaler fester Zeit (standard: UTC 2000-01-01 00:00:00)."""
        if fixed_time is None:
            fixed_time = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        elif fixed_time.tzinfo is None:
            raise ValueError("FakeTimeProvider erfordert tz-aware datetime")
        self._time = fixed_time

    def utc_now(self) -> datetime:
        """Liefere die vorgegebene oder setzte Zeit."""
        return self._time

    def set_time(self, new_time: datetime) -> None:
        """Setze eine neue Zeit (muss tz-aware sein)."""
        if new_time.tzinfo is None:
            raise ValueError("set_time erfordert tz-aware datetime")
        self._time = new_time
