"""Integration tests for i18n: Middleware + ResourceProvider + Exception Handlers."""

import pytest
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from src.shared_kernel.exception_handlers import register_exception_handlers
from src.shared_kernel.exceptions import DomainException
from src.shared_kernel.i18n import AcceptLanguageMiddleware


class TestI18nIntegration:
    """Integration tests for i18n functionality."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a test FastAPI app with all i18n components."""
        test_app = FastAPI()

        # Register exception handlers (which initializes ResourceProvider)
        register_exception_handlers(test_app)

        # Add Accept-Language middleware
        test_app.add_middleware(AcceptLanguageMiddleware)

        # Create a test endpoint that raises a DomainException
        @test_app.get("/test/user-not-found")
        async def user_not_found_endpoint(request: Request) -> JSONResponse:
            raise DomainException(
                "User with ID 12345 not found",
                error_type="https://api.example/errors/user-not-found",
                http_status=404,
                title="User not found (fallback)",
            )

        @test_app.get("/test/invalid-email")
        async def invalid_email_endpoint(request: Request) -> JSONResponse:
            raise DomainException(
                "Email address is not valid",
                error_type="https://api.example/errors/invalid-email",
                http_status=400,
                title="Invalid email (fallback)",
            )

        return test_app

    def test_domain_exception_de_DE_locale(self, app: FastAPI) -> None:
        """Test that domain exception is localized to German."""
        client = TestClient(app)
        response = client.get(
            "/test/user-not-found",
            headers={"Accept-Language": "de-DE"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["title"] == "Benutzer nicht gefunden"
        assert "user_id" in data["detail"].lower() or "benutzer" in data["detail"].lower()
        assert data["type"] == "https://api.example/errors/user-not-found"

    def test_domain_exception_en_US_locale(self, app: FastAPI) -> None:
        """Test that domain exception is localized to English."""
        client = TestClient(app)
        response = client.get(
            "/test/user-not-found",
            headers={"Accept-Language": "en-US"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["title"] == "User not found"
        assert "user" in data["detail"].lower()
        assert data["type"] == "https://api.example/errors/user-not-found"

    def test_domain_exception_default_locale_no_header(self, app: FastAPI) -> None:
        """Test that exception defaults to German when no Accept-Language header."""
        client = TestClient(app)
        response = client.get("/test/user-not-found")
        assert response.status_code == 404
        data = response.json()
        # Should use German (default) since no header provided
        assert data["title"] == "Benutzer nicht gefunden"

    def test_domain_exception_different_error_codes(self, app: FastAPI) -> None:
        """Test different error codes with localization."""
        client = TestClient(app)

        # Test INVALID_EMAIL in German
        response = client.get(
            "/test/invalid-email",
            headers={"Accept-Language": "de-DE"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["title"] == "Ungültige E-Mail-Adresse"
        assert data["type"] == "https://api.example/errors/invalid-email"

        # Test INVALID_EMAIL in English
        response = client.get(
            "/test/invalid-email",
            headers={"Accept-Language": "en-US"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["title"] == "Invalid email address"

    def test_domain_exception_multiple_language_preferences(self, app: FastAPI) -> None:
        """Test with multiple language preferences (RFC 7231)."""
        client = TestClient(app)
        response = client.get(
            "/test/user-not-found",
            headers={"Accept-Language": "en-US;q=0.9,de-DE;q=0.8"},
        )
        assert response.status_code == 404
        data = response.json()
        # Should use en-US since it has higher quality
        assert data["title"] == "User not found"

    def test_problem_details_format(self, app: FastAPI) -> None:
        """Test that response is RFC 7807 ProblemDetails format."""
        client = TestClient(app)
        response = client.get(
            "/test/user-not-found",
            headers={"Accept-Language": "de-DE"},
        )
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        # Verify all required fields
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data
        assert data["status"] == 404

    def test_fallback_to_default_locale_when_not_found(self, app: FastAPI) -> None:
        """Test fallback to de-DE when requested locale not in resources."""
        client = TestClient(app)
        response = client.get(
            "/test/user-not-found",
            headers={"Accept-Language": "fr-FR"},
        )
        assert response.status_code == 404
        data = response.json()
        # Should fall back to de-DE
        assert data["title"] == "Benutzer nicht gefunden"
