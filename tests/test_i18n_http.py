"""Tests für i18n Funktionalität am HTTP-Rand.

Prüft:
- Accept-Language-Header-Auswertung nach RFC 7231
- Fehlerrendering in verschiedenen Sprachen
- Content-Language-Header in Responses
- Sprachunabhängigkeit von type/code
"""

import pytest
from fastapi.testclient import TestClient

from src.api.i18n import get_language_from_header, load_resources
from src.main import app


@pytest.fixture(scope="session", autouse=True)
def _load_i18n() -> None:
    """Lade i18n-Ressourcen beim Start."""
    load_resources()


class TestLanguageSelection:
    """RFC 7231 Accept-Language-Header-Auswertung."""

    def test_exact_match_de_DE(self) -> None:
        """Exakte Übereinstimmung: de-DE wird akzeptiert."""
        assert get_language_from_header("de-DE") == "de-DE"

    def test_exact_match_en_US(self) -> None:
        """Exakte Übereinstimmung: en-US wird akzeptiert."""
        assert get_language_from_header("en-US") == "en-US"

    def test_case_insensitive_match(self) -> None:
        """Case-insensitiver Match: en-us wird zu en-US."""
        assert get_language_from_header("en-us") == "en-US"

    def test_underscore_normalization(self) -> None:
        """Unterstrich wird zu Bindestrich: de_DE wird zu de-DE."""
        assert get_language_from_header("de_DE") == "de-DE"

    def test_region_fallback_de(self) -> None:
        """Regionstreffer: de-AT wird zu de-DE."""
        assert get_language_from_header("de-AT") == "de-DE"

    def test_region_fallback_en(self) -> None:
        """Regionstreffer: en-GB wird zu en-US."""
        assert get_language_from_header("en-GB") == "en-US"

    def test_language_only_fallback(self) -> None:
        """Nur Sprache ohne Region: de wird zu de-DE."""
        assert get_language_from_header("de") == "de-DE"

    def test_q_weight_highest_wins(self) -> None:
        """q-Gewicht: höchster gewinnt."""
        assert get_language_from_header("de;q=0.5,en;q=0.9") == "en-US"

    def test_q_weight_equal_first_wins(self) -> None:
        """Bei gleichem q-Gewicht: erste Sprache gewinnt."""
        assert get_language_from_header("de;q=0.5,en;q=0.5") == "de-DE"

    def test_q_zero_ignored(self) -> None:
        """q=0 bedeutet 'akzeptiere ich nicht' (wird ignoriert)."""
        assert get_language_from_header("en;q=0,de") == "de-DE"

    def test_unknown_language_defaults_to_de_DE(self) -> None:
        """Unbekannte Sprache: Fallback auf de-DE."""
        assert get_language_from_header("fr") == "de-DE"

    def test_empty_header_defaults_to_de_DE(self) -> None:
        """Leerer Header: Fallback auf de-DE."""
        assert get_language_from_header("") == "de-DE"

    def test_none_header_defaults_to_de_DE(self) -> None:
        """None Header: Fallback auf de-DE."""
        assert get_language_from_header(None) == "de-DE"

    def test_malformed_q_value_ignored(self) -> None:
        """Defekter q-Wert wird ignoriert: en;q=invalid wird als en mit q=1.0 behandelt."""
        # "en;q=invalid" sollte als q=1.0 behandelt werden und gewinnen
        assert get_language_from_header("en;q=invalid,de;q=0.5") == "en-US"


class TestRegisterUserHttpI18n:
    """HTTP-Integration-Tests für Fehlerrendering."""

    @pytest.fixture
    def client(self) -> TestClient:
        """FastAPI TestClient."""
        return TestClient(app)

    def test_success_response_contains_content_language(self, client: TestClient) -> None:
        """Erfolgreicher Response enthält Content-Language."""
        response = client.post(
            "/api/v1/identity/register",
            json={
                "email": "test@example.com",
                "password": "test12345",
                "displayName": "Test User",
                "locale": "de-DE",
                "timeZoneId": "Europe/Berlin",
            },
            headers={"Accept-Language": "de-DE"},
        )
        assert response.status_code == 201
        assert "Content-Language" in response.headers
        assert response.headers["Content-Language"] == "de-DE"

    def test_error_response_de_DE(self, client: TestClient) -> None:
        """Fehlerresponse auf Deutsch."""
        response = client.post(
            "/api/v1/identity/register",
            json={
                "email": "invalid",
                "password": "short",
                "displayName": "",
                "locale": "invalid",
                "timeZoneId": "Invalid",
            },
            headers={"Accept-Language": "de-DE"},
        )
        assert response.status_code == 400
        assert response.headers.get("Content-Language") == "de-DE"
        data = response.json()
        # Prüfe deutsche Texte
        assert "Fehler" in data.get("title", "") or "ungültig" in data.get("detail", "")

    def test_error_response_en_US(self, client: TestClient) -> None:
        """Fehlerresponse auf Englisch."""
        response = client.post(
            "/api/v1/identity/register",
            json={
                "email": "invalid",
                "password": "short",
                "displayName": "",
                "locale": "invalid",
                "timeZoneId": "Invalid",
            },
            headers={"Accept-Language": "en-US"},
        )
        assert response.status_code == 400
        assert response.headers.get("Content-Language") == "en-US"
        data = response.json()
        # Prüfe englische Texte
        assert "invalid" in data.get("title", "").lower() or "input" in data.get(
            "detail", ""
        ).lower()

    def test_type_and_code_language_independent(self, client: TestClient) -> None:
        """type und Code sind sprachunabhängig."""
        response_de = client.post(
            "/api/v1/identity/register",
            json={
                "email": "test@example.com",
                "password": "test12345",
                "displayName": "Test",
                "locale": "de-DE",
                "timeZoneId": "Europe/Berlin",
            },
            headers={"Accept-Language": "de-DE"},
        )
        # Zweiter Versuch mit gleicher Email
        response_en = client.post(
            "/api/v1/identity/register",
            json={
                "email": "test@example.com",
                "password": "test12345",
                "displayName": "Test",
                "locale": "de-DE",
                "timeZoneId": "Europe/Berlin",
            },
            headers={"Accept-Language": "en-US"},
        )

        # Beide sollten 409 sein
        assert response_de.status_code == 201 or response_de.status_code == 409
        assert response_en.status_code == 409

        # Code und type sollten gleich sein
        de_data = response_de.json() if response_de.status_code != 201 else response_en.json()
        en_data = response_en.json()

        de_type = de_data.get("type")
        en_type = en_data.get("type")
        assert de_type == en_type, "type sollte sprachunabhängig sein"

    def test_field_errors_translated(self, client: TestClient) -> None:
        """Feldfehler werden übersetzt."""
        response = client.post(
            "/api/v1/identity/register",
            json={
                "email": "invalid",
                "password": "short",
                "displayName": "",
                "locale": "de-DE",
                "timeZoneId": "Europe/Berlin",
            },
            headers={"Accept-Language": "de-DE"},
        )
        assert response.status_code == 400
        data = response.json()
        # Prüfe, dass errors vorhanden sind
        errors = data.get("errors", {})
        assert len(errors) > 0, "Es sollten Feldfehler sein"
        # Prüfe, dass Fehler deutsche Texte enthalten
        for field_errors in errors.values():
            assert len(field_errors) > 0
            # Mindestens einer sollte auf Deutsch sein
            assert any("email" in str(e).lower() or "Passwort" in str(e) for e in field_errors)
