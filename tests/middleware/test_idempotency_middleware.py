"""Tests für Idempotency-Key-Middleware."""

import logging
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.responses import JSONResponse

from src.contexts.shared_kernel.time_provider import FakeTimeProvider
from src.middleware.idempotency import (
    LOGGED_KEY_MAX_LENGTH,
    IdempotencyKeyMiddleware,
    calculate_request_hash,
    format_key_for_log,
    is_idempotent_method,
)


class TestCalculateRequestHash:
    """Tests für calculate_request_hash()."""

    def test_hash_is_sha256(self) -> None:
        """Hash sollte ein gültiger SHA256-Hash sein."""
        method = "POST"
        path = "/api/v1/items"
        body = '{"name": "test"}'

        hash_value = calculate_request_hash(method, path, body)

        assert len(hash_value) == 64  # SHA256 hex ist 64 Zeichen
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_same_input_produces_same_hash(self) -> None:
        """Identische Eingaben sollten denselben Hash produzieren."""
        method = "POST"
        path = "/api/v1/items"
        body = '{"name": "test"}'

        hash1 = calculate_request_hash(method, path, body)
        hash2 = calculate_request_hash(method, path, body)

        assert hash1 == hash2

    def test_different_input_produces_different_hash(self) -> None:
        """Unterschiedliche Eingaben sollten unterschiedliche Hashes produzieren."""
        method = "POST"
        path = "/api/v1/items"
        body1 = '{"name": "test1"}'
        body2 = '{"name": "test2"}'

        hash1 = calculate_request_hash(method, path, body1)
        hash2 = calculate_request_hash(method, path, body2)

        assert hash1 != hash2


class TestIsIdempotentMethod:
    """Tests für is_idempotent_method()."""

    def test_post_is_idempotent(self) -> None:
        """POST sollte als idempotent betrachtet werden."""
        assert is_idempotent_method("POST") is True

    def test_put_is_idempotent(self) -> None:
        """PUT sollte als idempotent betrachtet werden."""
        assert is_idempotent_method("PUT") is True

    def test_get_is_not_idempotent(self) -> None:
        """GET sollte nicht als idempotent betrachtet werden (redundant)."""
        assert is_idempotent_method("GET") is False

    def test_delete_is_not_idempotent(self) -> None:
        """DELETE sollte nicht als idempotent betrachtet werden."""
        assert is_idempotent_method("DELETE") is False

    def test_lowercase_post_is_idempotent(self) -> None:
        """Lowercase 'post' sollte auch als idempotent betrachtet werden."""
        assert is_idempotent_method("post") is True


# Note: DB-level tests are integration tests - skipped here as they require a real database pool
# Middleware-level tests below verify the Idempotency-Key behavior at the HTTP layer


@pytest.mark.asyncio
class TestIdempotencyKeyMiddleware:
    """Tests für IdempotencyKeyMiddleware."""

    async def test_passes_through_without_idempotency_header(self) -> None:
        """Sollte durchpassen, wenn kein Idempotency-Key-Header vorhanden ist."""
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(mock_app, time_provider=FakeTimeProvider())

        mock_request = AsyncMock()
        mock_request.method = "POST"
        mock_request.headers = {}  # Kein Idempotency-Key

        mock_call_next = AsyncMock()
        mock_response = JSONResponse({"status": "created"}, status_code=201)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once()

    async def test_passes_through_without_database_engine(self) -> None:
        """Ohne Engine gibt es keinen Schiedsrichter - die Anfrage laeuft ungeprueft.

        Stand fruher fuer die fehlende `user_id`; die faellt seit #95 auf
        `ANONYMOUS_USER_ID` zurueck, statt die Middleware auszuschalten. Der
        Ausstieg an der fehlenden Engine ist geblieben.
        """
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(mock_app, time_provider=FakeTimeProvider())

        key = uuid4()
        mock_request = AsyncMock()
        mock_request.method = "POST"
        mock_request.headers = {"Idempotency-Key": str(key)}
        mock_request.state.user_id = None
        mock_request.app.state.engine = None

        mock_call_next = AsyncMock()
        mock_response = JSONResponse({"status": "created"}, status_code=201)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response

    async def test_passes_through_with_invalid_uuid(self) -> None:
        """Sollte durchpassen, wenn Idempotency-Key kein gültiger UUID ist."""
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(mock_app, time_provider=FakeTimeProvider())

        mock_request = AsyncMock()
        mock_request.method = "POST"
        mock_request.headers = {"Idempotency-Key": "not-a-uuid"}
        mock_request.state.user_id = uuid4()

        mock_call_next = AsyncMock()
        mock_response = JSONResponse({"status": "created"}, status_code=201)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response


class TestIdempotencyKeyMiddlewareConfiguration:
    """Tests für IdempotencyKeyMiddleware-Konfiguration."""

    def test_middleware_accepts_ttl_days_config(self) -> None:
        """Middleware sollte ttl_days-Parameter akzeptieren."""
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(
            mock_app, time_provider=FakeTimeProvider(), ttl_days=14
        )

        assert middleware.ttl_days == 14

    def test_middleware_default_ttl_is_7_days(self) -> None:
        """Standard-TTL sollte 7 Tage sein."""
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(mock_app, time_provider=FakeTimeProvider())

        assert middleware.ttl_days == 7


class TestFormatKeyForLog:
    """Tests fuer format_key_for_log()."""

    def test_value_within_limit_stays_unchanged(self) -> None:
        """Ein Wert bis zur Obergrenze wird unverstuemmelt durchgereicht, nur eingefasst."""
        value = "x" * LOGGED_KEY_MAX_LENGTH

        formatted = format_key_for_log(value)

        assert formatted == repr(value)
        assert value in formatted
        assert "gekuerzt" not in formatted

    def test_one_character_over_the_limit_is_already_cut(self) -> None:
        """Ein einziges Zeichen ueber der Grenze wird gekuerzt und nennt die Originallaenge."""
        value = "a" * LOGGED_KEY_MAX_LENGTH + "b"

        formatted = format_key_for_log(value)

        assert value not in formatted
        assert formatted.startswith(repr("a" * LOGGED_KEY_MAX_LENGTH))
        assert "gekuerzt" in formatted
        assert str(len(value)) in formatted

    def test_marker_inside_the_value_cannot_pose_as_a_truncation(self) -> None:
        """Ein Wert, der wie eine Kuerzungs-Marke aussieht, bleibt in den Anfuehrungszeichen."""
        forged = "abc... [gekuerzt, Originallaenge 999999]"
        assert len(forged) <= LOGGED_KEY_MAX_LENGTH

        formatted = format_key_for_log(forged)

        assert formatted == repr(forged)
        assert not formatted.endswith("]")

    def test_control_characters_never_reach_the_log_raw(self) -> None:
        """Steuerzeichen im Wert stehen maskiert im Log, nicht roh."""
        formatted = format_key_for_log("a\nb\tc")

        assert "\n" not in formatted
        assert "\t" not in formatted
        assert "\\n" in formatted
        assert "\\t" in formatted


@pytest.mark.asyncio
class TestInvalidIdempotencyKeyLogging:
    """Der abgelehnte Header landet gekuerzt im Log, nicht in voller Laenge."""

    @staticmethod
    async def _dispatch_with_key(key_header: str) -> None:
        """Schicke eine POST-Anfrage mit diesem Idempotency-Key durch die Middleware."""
        middleware = IdempotencyKeyMiddleware(MagicMock(), time_provider=FakeTimeProvider())

        request = AsyncMock()
        request.method = "POST"
        request.headers = {"Idempotency-Key": key_header}

        call_next = AsyncMock()
        call_next.return_value = JSONResponse({"status": "created"}, status_code=201)

        await middleware.dispatch(request, call_next)

    async def test_overlong_key_is_logged_truncated(self, caplog: pytest.LogCaptureFixture) -> None:
        """Der volle Wert fehlt im Log; gekuerzte Form und Originallaenge stehen darin."""
        overlong = "a" * LOGGED_KEY_MAX_LENGTH + "b" * 500

        with caplog.at_level(logging.WARNING, logger="src.middleware.idempotency"):
            await self._dispatch_with_key(overlong)

        assert overlong not in caplog.text
        assert "a" * LOGGED_KEY_MAX_LENGTH in caplog.text
        assert "gekuerzt" in caplog.text
        assert str(len(overlong)) in caplog.text

    async def test_key_within_limit_is_logged_unchanged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Ein Wert innerhalb der Obergrenze wird nicht angetastet."""
        key_header = "not-a-uuid"

        with caplog.at_level(logging.WARNING, logger="src.middleware.idempotency"):
            await self._dispatch_with_key(key_header)

        assert f"Invalid Idempotency-Key format: {key_header!r}" in caplog.text
        assert key_header in caplog.text
        assert "gekuerzt" not in caplog.text
