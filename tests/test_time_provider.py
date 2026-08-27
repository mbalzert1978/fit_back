"""Unit-Tests für TimeProvider."""

from datetime import UTC, datetime

import pytest

from src.contexts.shared_kernel.time_provider import FakeTimeProvider, SystemTimeProvider


class TestSystemTimeProvider:
    """Tests für SystemTimeProvider."""

    def test_utc_now_returns_tz_aware_datetime(self) -> None:
        provider = SystemTimeProvider()
        now = provider.utc_now()

        assert isinstance(now, datetime)
        assert now.tzinfo is not None
        assert now.tzinfo == UTC

    def test_utc_now_returns_reasonable_time(self) -> None:
        provider = SystemTimeProvider()
        before = datetime.now(UTC)
        now = provider.utc_now()
        after = datetime.now(UTC)

        assert before <= now <= after

    def test_multiple_calls_increase_time(self) -> None:
        provider = SystemTimeProvider()
        time1 = provider.utc_now()
        time2 = provider.utc_now()

        # time2 sollte >= time1 sein (erlaubt gleiche Zeit bei sehr schnellen Aufrufen)
        assert time2 >= time1


class TestFakeTimeProvider:
    """Tests für FakeTimeProvider."""

    def test_default_initialization(self) -> None:
        """Ohne Parameter sollte FakeTimeProvider auf 2000-01-01 00:00:00 UTC initialisieren."""
        provider = FakeTimeProvider()
        now = provider.utc_now()

        assert now == datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_custom_initialization(self) -> None:
        fixed_time = datetime(2025, 8, 5, 12, 30, 45, tzinfo=UTC)
        provider = FakeTimeProvider(fixed_time)
        now = provider.utc_now()

        assert now == fixed_time

    def test_initialization_rejects_naive_datetime(self) -> None:
        """FakeTimeProvider sollte naïve datetime (ohne Timezone) ablehnen."""
        naive_time = datetime(2025, 8, 5, 12, 30, 45)  # noqa: DTZ001 - bewusst naiv, testet die Ablehnung

        with pytest.raises(ValueError, match="tz-aware"):
            FakeTimeProvider(naive_time)

    def test_set_time_updates_current_time(self) -> None:
        provider = FakeTimeProvider()
        new_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

        provider.set_time(new_time)
        assert provider.utc_now() == new_time

    def test_set_time_rejects_naive_datetime(self) -> None:
        provider = FakeTimeProvider()
        naive_time = datetime(2025, 8, 5, 12, 30, 45)  # noqa: DTZ001 - bewusst naiv, testet die Ablehnung

        with pytest.raises(ValueError, match="tz-aware"):
            provider.set_time(naive_time)

    def test_fake_time_is_deterministic(self) -> None:
        fixed_time = datetime(2025, 8, 5, 12, 30, 45, tzinfo=UTC)
        provider = FakeTimeProvider(fixed_time)

        time1 = provider.utc_now()
        time2 = provider.utc_now()
        time3 = provider.utc_now()

        assert time1 == time2 == time3 == fixed_time

    def test_fake_time_sequence(self) -> None:
        provider = FakeTimeProvider(datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC))

        time1 = provider.utc_now()
        new_time = datetime(2025, 1, 1, 1, 0, 0, tzinfo=UTC)
        provider.set_time(new_time)
        time2 = provider.utc_now()

        assert time1 < time2
        assert time2 == new_time
