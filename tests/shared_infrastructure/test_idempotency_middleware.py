"""Tests für Idempotency-Key-Middleware."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.responses import JSONResponse

from src.shared_infrastructure.idempotency import (
    IdempotencyKeyMiddleware,
    calculate_request_hash,
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
        middleware = IdempotencyKeyMiddleware(mock_app)

        mock_request = AsyncMock()
        mock_request.method = "POST"
        mock_request.headers = {}  # Kein Idempotency-Key

        mock_call_next = AsyncMock()
        mock_response = JSONResponse({"status": "created"}, status_code=201)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once()

    async def test_passes_through_without_user_id(self) -> None:
        """Sollte durchpassen, wenn keine user_id in request.state vorhanden ist."""
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(mock_app)

        key = uuid4()
        mock_request = AsyncMock()
        mock_request.method = "POST"
        mock_request.headers = {"Idempotency-Key": str(key)}
        mock_request.state.user_id = None

        mock_call_next = AsyncMock()
        mock_response = JSONResponse({"status": "created"}, status_code=201)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response

    async def test_passes_through_with_invalid_uuid(self) -> None:
        """Sollte durchpassen, wenn Idempotency-Key kein gültiger UUID ist."""
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(mock_app)

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
        middleware = IdempotencyKeyMiddleware(mock_app, ttl_days=14)

        assert middleware.ttl_days == 14

    def test_middleware_default_ttl_is_7_days(self) -> None:
        """Standard-TTL sollte 7 Tage sein."""
        mock_app = MagicMock()
        middleware = IdempotencyKeyMiddleware(mock_app)

        assert middleware.ttl_days == 7
