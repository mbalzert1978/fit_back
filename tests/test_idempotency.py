"""Tests for Idempotency-Key middleware."""

import asyncio
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from src.shared_kernel.idempotency import IdempotencyKeyMiddleware
from src.shared_kernel.time_provider import FakeTimeProvider


@pytest.fixture
def fake_time_provider() -> FakeTimeProvider:
    """Provide a FakeTimeProvider for deterministic testing."""
    return FakeTimeProvider()


@pytest.fixture
def test_app(
    db_pool: object,
    fake_time_provider: FakeTimeProvider,
) -> FastAPI:
    """Create a test FastAPI app with idempotency middleware.

    Note: db_pool is a fixture that should be provided by conftest.py
    """
    app = FastAPI()

    # Add a simple test endpoint that returns a JSON response
    @app.post("/api/v1/test-idempotency")
    async def test_endpoint() -> JSONResponse:
        """Test endpoint that simulates resource creation."""
        user_id = uuid4()
        return JSONResponse(
            status_code=201,
            content={
                "id": str(user_id),
                "data": "test-response",
                "timestamp": fake_time_provider.utc_now().isoformat(),
            },
        )

    # Add idempotency middleware
    # Note: In production, this is registered in lifespan; here we add it directly
    if db_pool is not None:
        app.add_middleware(
            IdempotencyKeyMiddleware,
            db_pool=db_pool,
            time_provider=fake_time_provider,
        )

    return app


@pytest.mark.asyncio
class TestIdempotencyKeyMiddleware:
    """Test Idempotency-Key middleware behavior."""

    async def test_request_without_idempotency_key_passes_through(
        self,
        test_app: FastAPI,
    ) -> None:
        """Requests without Idempotency-Key header should pass through normally."""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/test-idempotency")
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["data"] == "test-response"

    async def test_idempotency_key_with_unauthenticated_request(
        self,
        test_app: FastAPI,
    ) -> None:
        """Requests with Idempotency-Key but without auth should pass through."""
        idempotency_key = str(uuid4())
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": idempotency_key},
            )
            assert response.status_code == 201

    async def test_idempotency_key_cache_hit_with_same_key(
        self,
        test_app: FastAPI,
        db_pool: object,
    ) -> None:
        """Second request with same Idempotency-Key should return cached 200.

        NOTE: This test requires a real database pool and migration setup.
        Without proper DB initialization, this will be skipped.
        """
        if db_pool is None:
            pytest.skip("Database pool not available")

        idempotency_key = str(uuid4())
        user_id = uuid4()

        # Create a modified test app that simulates auth
        app = FastAPI()

        @app.post("/api/v1/test-idempotency")
        async def test_endpoint() -> JSONResponse:
            """Test endpoint with authenticated user."""
            return JSONResponse(
                status_code=201,
                content={
                    "id": str(uuid4()),
                    "data": "cached-response",
                },
            )

        # Middleware that injects user_id
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import Response

        class AuthMiddleware(BaseHTTPMiddleware):
            """Inject user_id into request state."""

            async def dispatch(
                self,
                request,  # type: ignore[no-untyped-def]
                call_next,  # type: ignore[no-untyped-def]
            ) -> Response:
                request.state.user_id = user_id
                return await call_next(request)  # type: ignore[no-untyped-call]

        app.add_middleware(AuthMiddleware)
        app.add_middleware(
            IdempotencyKeyMiddleware,
            db_pool=db_pool,
            time_provider=FakeTimeProvider(),
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First request
            response1 = await client.post(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": idempotency_key},
            )
            assert response1.status_code == 201
            data1 = response1.json()

            # Small delay to ensure DB write completes
            await asyncio.sleep(0.1)

            # Second request with same key should return 200
            response2 = await client.post(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": idempotency_key},
            )
            # On cache hit, should return 200 (not original 201)
            assert response2.status_code == 200
            data2 = response2.json()
            # Cached response should match original
            assert data1 == data2

    async def test_different_idempotency_keys_create_separate_entries(
        self,
        test_app: FastAPI,
    ) -> None:
        """Different Idempotency-Keys should not interfere."""
        key1 = str(uuid4())
        key2 = str(uuid4())

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response1 = await client.post(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": key1},
            )
            assert response1.status_code == 201

            response2 = await client.post(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": key2},
            )
            # Both should return 201 (no cache hit because keys differ)
            assert response2.status_code == 201

    async def test_put_request_with_idempotency_key(
        self,
        test_app: FastAPI,
    ) -> None:
        """PUT requests with Idempotency-Key should also be handled."""

        # Add a PUT endpoint
        @test_app.put("/api/v1/test-idempotency")
        async def put_endpoint() -> JSONResponse:
            return JSONResponse(
                status_code=200,
                content={"updated": True},
            )

        idempotency_key = str(uuid4())
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": idempotency_key},
            )
            # Without auth, should pass through
            assert response.status_code == 200

    async def test_invalid_idempotency_key_uuid_passes_through(
        self,
        test_app: FastAPI,
    ) -> None:
        """Invalid UUID in Idempotency-Key should not crash, just pass through."""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": "not-a-uuid"},
            )
            # Should still return 201 (middleware warning logged, request continues)
            assert response.status_code == 201

    async def test_get_request_ignores_idempotency_key(
        self,
        test_app: FastAPI,
    ) -> None:
        """GET requests with Idempotency-Key should be ignored (only POST/PUT)."""

        # Add a GET endpoint
        @test_app.get("/api/v1/test-idempotency")
        async def get_endpoint() -> JSONResponse:
            return JSONResponse(status_code=200, content={"data": "test"})

        idempotency_key = str(uuid4())
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/test-idempotency",
                headers={"Idempotency-Key": idempotency_key},
            )
            assert response.status_code == 200
