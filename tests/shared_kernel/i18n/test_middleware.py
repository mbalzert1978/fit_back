"""Tests for Accept-Language middleware."""

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from src.shared_kernel.i18n.middleware import (
    LocalePreference,
    parse_accept_language_header,
)


class TestLocalePreference:
    """Test suite for LocalePreference data class."""

    def test_locale_preference_creation(self) -> None:
        """Test creating a LocalePreference."""
        pref = LocalePreference("de-DE", 1.0)
        assert pref.locale == "de-DE"
        assert pref.quality == 1.0

    def test_locale_preference_default_quality(self) -> None:
        """Test that default quality is 1.0."""
        pref = LocalePreference("de-DE")
        assert pref.quality == 1.0

    def test_locale_preference_comparison(self) -> None:
        """Test comparison of LocalePreference by quality (higher first)."""
        pref1 = LocalePreference("de-DE", 1.0)
        pref2 = LocalePreference("en-US", 0.9)
        # pref1 should be "less than" pref2 in sorting (higher quality = comes first)
        assert pref2 > pref1


class TestParseAcceptLanguageHeader:
    """Test suite for parsing Accept-Language header."""

    def test_parse_single_locale(self) -> None:
        """Test parsing single locale."""
        prefs = parse_accept_language_header("de-DE")
        assert len(prefs) == 1
        assert prefs[0].locale == "de-DE"
        assert prefs[0].quality == 1.0

    def test_parse_multiple_locales(self) -> None:
        """Test parsing multiple locales."""
        prefs = parse_accept_language_header("de-DE,en-US")
        assert len(prefs) == 2
        assert prefs[0].locale == "de-DE"
        assert prefs[1].locale == "en-US"

    def test_parse_with_quality_factors(self) -> None:
        """Test parsing locales with quality factors."""
        prefs = parse_accept_language_header("de-DE,en-US;q=0.9")
        assert len(prefs) == 2
        assert prefs[0].locale == "de-DE"
        assert prefs[0].quality == 1.0
        assert prefs[1].locale == "en-US"
        assert prefs[1].quality == 0.9

    def test_parse_sorted_by_quality(self) -> None:
        """Test that results are sorted by quality (highest first)."""
        prefs = parse_accept_language_header("en-US;q=0.5,de-DE;q=0.9,fr-FR")
        assert len(prefs) == 3
        assert prefs[0].locale == "fr-FR"
        assert prefs[0].quality == 1.0
        assert prefs[1].locale == "de-DE"
        assert prefs[1].quality == 0.9
        assert prefs[2].locale == "en-US"
        assert prefs[2].quality == 0.5

    def test_parse_with_whitespace(self) -> None:
        """Test parsing with various whitespace."""
        prefs = parse_accept_language_header("  de-DE  ,  en-US  ;  q=0.8  ")
        assert len(prefs) == 2
        assert prefs[0].locale == "de-DE"
        assert prefs[1].locale == "en-US"

    def test_parse_quality_clamping(self) -> None:
        """Test that quality values are clamped to [0, 1]."""
        prefs = parse_accept_language_header("de-DE;q=1.5")
        assert prefs[0].quality == 1.0

        prefs = parse_accept_language_header("de-DE;q=-0.5")
        assert prefs[0].quality == 0.0

    def test_parse_invalid_quality(self) -> None:
        """Test handling of invalid quality values."""
        # Invalid quality should be treated as default 1.0
        prefs = parse_accept_language_header("de-DE;q=invalid")
        assert len(prefs) == 1
        assert prefs[0].quality == 1.0

    def test_parse_empty_string(self) -> None:
        """Test parsing empty header."""
        prefs = parse_accept_language_header("")
        assert len(prefs) == 0

    def test_parse_empty_preferences(self) -> None:
        """Test parsing with only commas."""
        prefs = parse_accept_language_header(",,,")
        assert len(prefs) == 0


class TestAcceptLanguageMiddleware:
    """Test suite for AcceptLanguageMiddleware integration."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a test FastAPI app with middleware."""
        from src.shared_kernel.i18n import AcceptLanguageMiddleware

        test_app = FastAPI()

        @test_app.get("/test")
        async def test_endpoint(request: Request) -> JSONResponse:
            locale = getattr(request.state, "locale", "not-set")
            return JSONResponse({"locale": locale})

        test_app.add_middleware(AcceptLanguageMiddleware)
        return test_app

    def test_middleware_default_locale(self, app: FastAPI) -> None:
        """Test middleware uses de-DE when no Accept-Language header."""
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json()["locale"] == "de-DE"

    def test_middleware_with_de_DE_header(self, app: FastAPI) -> None:
        """Test middleware with German locale header."""
        client = TestClient(app)
        response = client.get("/test", headers={"Accept-Language": "de-DE"})
        assert response.status_code == 200
        assert response.json()["locale"] == "de-DE"

    def test_middleware_with_en_US_header(self, app: FastAPI) -> None:
        """Test middleware with English locale header."""
        client = TestClient(app)
        response = client.get("/test", headers={"Accept-Language": "en-US"})
        assert response.status_code == 200
        assert response.json()["locale"] == "en-US"

    def test_middleware_with_multiple_locales(self, app: FastAPI) -> None:
        """Test middleware selects highest priority from multiple locales."""
        client = TestClient(app)
        response = client.get(
            "/test",
            headers={"Accept-Language": "en-US;q=0.9,de-DE;q=0.5"},
        )
        assert response.status_code == 200
        assert response.json()["locale"] == "en-US"

    def test_middleware_normalizes_locale(self, app: FastAPI) -> None:
        """Test middleware normalizes single language codes."""
        client = TestClient(app)
        # Send "en" which should be normalized to "en-US"
        response = client.get("/test", headers={"Accept-Language": "en"})
        assert response.status_code == 200
        assert response.json()["locale"] == "en-US"

    def test_middleware_normalizes_de_to_de_DE(self, app: FastAPI) -> None:
        """Test middleware normalizes 'de' to 'de-DE'."""
        client = TestClient(app)
        response = client.get("/test", headers={"Accept-Language": "de"})
        assert response.status_code == 200
        assert response.json()["locale"] == "de-DE"

    def test_middleware_normalizes_uppercase_region(self, app: FastAPI) -> None:
        """Test middleware normalizes region to uppercase."""
        client = TestClient(app)
        response = client.get("/test", headers={"Accept-Language": "de-de"})
        assert response.status_code == 200
        assert response.json()["locale"] == "de-DE"

    def test_middleware_case_insensitive_header(self, app: FastAPI) -> None:
        """Test middleware handles case variations."""
        client = TestClient(app)
        response = client.get("/test", headers={"Accept-Language": "De-De"})
        assert response.status_code == 200
        assert response.json()["locale"] == "de-DE"
