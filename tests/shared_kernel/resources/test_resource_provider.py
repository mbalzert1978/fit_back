"""Tests for ResourceProvider and Locale value object."""

import json
import tempfile
from pathlib import Path

import pytest

from src.shared_kernel.resources import Locale, ResourceProvider


class TestLocale:
    """Test suite for Locale value object."""

    def test_locale_creation(self) -> None:
        """Test creating a Locale instance."""
        locale = Locale("de", "DE")
        assert locale.language == "de"
        assert locale.region == "DE"

    def test_locale_string_representation(self) -> None:
        """Test string representation of Locale."""
        locale = Locale("de", "DE")
        assert str(locale) == "de-DE"

    def test_locale_parse_valid(self) -> None:
        """Test parsing valid locale strings."""
        locale = Locale.parse("de-DE")
        assert locale.language == "de"
        assert locale.region == "DE"

        locale = Locale.parse("en-US")
        assert locale.language == "en"
        assert locale.region == "US"

    def test_locale_parse_lowercasing(self) -> None:
        """Test that parse lowercases language codes."""
        locale = Locale.parse("DE-DE")
        assert locale.language == "de"
        assert locale.region == "DE"

    def test_locale_parse_invalid_format(self) -> None:
        """Test parsing invalid locale formats."""
        with pytest.raises(ValueError, match="Invalid locale format"):
            Locale.parse("de")

        with pytest.raises(ValueError, match="Invalid locale format"):
            Locale.parse("de-DE-extra")

        with pytest.raises(ValueError, match="must not be empty"):
            Locale.parse("-DE")

    def test_locale_frozen(self) -> None:
        """Test that Locale is immutable."""
        locale = Locale("de", "DE")
        with pytest.raises(AttributeError):
            locale.language = "en"  # type: ignore[misc]


class TestResourceProvider:
    """Test suite for ResourceProvider."""

    @pytest.fixture
    def temp_resources(self) -> Path:
        """Create temporary resource files for testing."""
        tmpdir = Path(tempfile.gettempdir()) / "test_resources"
        tmpdir.mkdir(exist_ok=True)

        # Create German resource file
        de_resources = {
            "USER_NOT_FOUND": {
                "title": "Benutzer nicht gefunden",
                "detail": "Der Benutzer mit der ID {user_id} existiert nicht.",
            },
            "INVALID_EMAIL": {
                "title": "Ungültige E-Mail",
                "detail": "Die E-Mail '{email}' ist nicht gültig.",
            },
        }
        with open(tmpdir / "errors_de_DE.json", "w", encoding="utf-8") as f:
            json.dump(de_resources, f)

        # Create English resource file
        en_resources = {
            "USER_NOT_FOUND": {
                "title": "User not found",
                "detail": "The user with ID {user_id} does not exist.",
            },
            "INVALID_EMAIL": {
                "title": "Invalid email",
                "detail": "The email '{email}' is not valid.",
            },
        }
        with open(tmpdir / "errors_en_US.json", "w", encoding="utf-8") as f:
            json.dump(en_resources, f)

        yield tmpdir

        # Cleanup
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_resource_provider_initialization(self, temp_resources: Path) -> None:
        """Test ResourceProvider initialization."""
        provider = ResourceProvider(temp_resources)
        assert provider.resources_dir == temp_resources

    def test_get_message_de_DE(self, temp_resources: Path) -> None:
        """Test getting German message."""
        provider = ResourceProvider(temp_resources)
        message = provider.get_message("USER_NOT_FOUND", "de-DE")
        assert message["title"] == "Benutzer nicht gefunden"
        assert "user_id" in message["detail"]

    def test_get_message_en_US(self, temp_resources: Path) -> None:
        """Test getting English message."""
        provider = ResourceProvider(temp_resources)
        message = provider.get_message("USER_NOT_FOUND", "en-US")
        assert message["title"] == "User not found"
        assert "user_id" in message["detail"]

    def test_get_message_with_None_locale_uses_default(self, temp_resources: Path) -> None:
        """Test that None locale falls back to default (de-DE)."""
        provider = ResourceProvider(temp_resources)
        message = provider.get_message("USER_NOT_FOUND", None)
        assert message["title"] == "Benutzer nicht gefunden"

    def test_get_message_fallback_to_default_locale(self, temp_resources: Path) -> None:
        """Test fallback to de-DE when requested locale not found."""
        provider = ResourceProvider(temp_resources)
        # Request fr-FR which doesn't exist, should fall back to de-DE
        message = provider.get_message("USER_NOT_FOUND", "fr-FR")
        assert message["title"] == "Benutzer nicht gefunden"

    def test_get_message_invalid_locale_falls_back(self, temp_resources: Path) -> None:
        """Test that invalid locale format falls back to default."""
        provider = ResourceProvider(temp_resources)
        message = provider.get_message("USER_NOT_FOUND", "invalid")
        assert message["title"] == "Benutzer nicht gefunden"

    def test_get_message_missing_error_code(self, temp_resources: Path) -> None:
        """Test getting message for non-existent error code."""
        provider = ResourceProvider(temp_resources)
        message = provider.get_message("NON_EXISTENT_ERROR", "de-DE")
        assert message == {"title": "", "detail": ""}

    def test_get_message_caching(self, temp_resources: Path) -> None:
        """Test that resource files are cached."""
        provider = ResourceProvider(temp_resources)
        # Load the same file twice
        message1 = provider.get_message("USER_NOT_FOUND", "de-DE")
        message2 = provider.get_message("USER_NOT_FOUND", "de-DE")
        # Both should be identical (from cache)
        assert message1 == message2
        # Verify cache is populated
        assert "de-DE" in provider._cache

    def test_get_message_multiple_locales(self, temp_resources: Path) -> None:
        """Test accessing multiple locales."""
        provider = ResourceProvider(temp_resources)
        de_message = provider.get_message("INVALID_EMAIL", "de-DE")
        en_message = provider.get_message("INVALID_EMAIL", "en-US")
        assert de_message["title"] == "Ungültige E-Mail"
        assert en_message["title"] == "Invalid email"

    def test_default_locale_is_de_DE(self, temp_resources: Path) -> None:
        """Test that default locale is de-DE."""
        provider = ResourceProvider(temp_resources)
        assert provider._default_locale == Locale("de", "DE")
