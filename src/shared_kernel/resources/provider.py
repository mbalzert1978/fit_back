"""Resource provider for loading and caching localized error messages."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import final

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Locale:
    """Locale value object representing language and region.

    Example: Locale("de", "DE") for German (Germany).
    """

    language: str
    region: str

    def __str__(self) -> str:
        """Return locale string in format: language-REGION."""
        return f"{self.language}-{self.region}"

    @staticmethod
    def parse(locale_str: str) -> "Locale":
        """Parse locale from string format (e.g., 'de-DE', 'en-US').

        Args:
            locale_str: Locale string in format 'language-REGION'

        Returns:
            Parsed Locale object

        Raises:
            ValueError: If locale string format is invalid
        """
        parts = locale_str.split("-")
        if len(parts) != 2:
            msg = f"Invalid locale format: {locale_str}. Expected format: language-REGION"
            raise ValueError(msg)
        language, region = parts
        if not language or not region:
            msg = f"Invalid locale format: {locale_str}. Language and region must not be empty"
            raise ValueError(msg)
        return Locale(language.lower(), region.upper())


@final
class ResourceProvider:
    """Provider for loading and caching localized resource files.

    Loads error messages from JSON files in a centralized location and
    provides fallback logic for missing locales and keys.
    """

    def __init__(self, resources_dir: str | Path | None = None) -> None:
        """Initialize ResourceProvider.

        Args:
            resources_dir: Path to resources directory. Defaults to
                          src/shared_kernel/resources/
        """
        if resources_dir is None:
            # Default to the resources directory relative to this module
            resources_dir = Path(__file__).parent
        else:
            resources_dir = Path(resources_dir)

        self.resources_dir = resources_dir
        self._cache: dict[str, dict[str, dict[str, str]]] = {}
        self._default_locale = Locale("de", "DE")
        logger.debug(f"ResourceProvider initialized with directory: {resources_dir}")

    def _load_locale(self, locale: Locale) -> dict[str, dict[str, str]]:
        """Load error messages for a specific locale from JSON file.

        Args:
            locale: Locale object to load

        Returns:
            Dictionary with error code -> {title, detail} mapping
        """
        locale_key = str(locale)
        if locale_key in self._cache:
            return self._cache[locale_key]

        # Filename uses underscore: errors_de_DE.json not errors_de-DE.json
        filename = f"errors_{locale.language}_{locale.region}.json"
        filepath = self.resources_dir / filename

        if not filepath.exists():
            logger.warning(f"Resource file not found: {filepath}")
            return {}

        try:
            with open(filepath, encoding="utf-8") as f:
                data: dict[str, dict[str, str]] = json.load(f)
            self._cache[str(locale)] = data
            logger.debug(f"Loaded resource file: {filename}")
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading resource file {filename}: {e}")
            return {}

    def get_message(self, error_code: str, locale_str: str | None = None) -> dict[str, str]:
        """Get localized error message for an error code.

        Implements fallback logic:
        1. Try requested locale
        2. Fall back to de-DE if requested locale not found
        3. Return empty title/detail if error code not found in any locale

        Args:
            error_code: Error code to look up (e.g., 'USER_NOT_FOUND')
            locale_str: Locale string in format 'language-REGION'.
                       Defaults to 'de-DE' if not provided.

        Returns:
            Dictionary with 'title' and 'detail' keys. Returns
            {'title': '', 'detail': ''} if error code not found.
        """
        if locale_str is None:
            locale_str = str(self._default_locale)

        # Parse locale string, fall back to default if invalid
        try:
            requested_locale = Locale.parse(locale_str)
        except ValueError:
            logger.warning(f"Invalid locale string: {locale_str}, using default")
            requested_locale = self._default_locale

        # Try to load requested locale
        messages = self._load_locale(requested_locale)

        # If locale not found or error code not in locale, try default locale
        if error_code not in messages and requested_locale != self._default_locale:
            logger.debug(
                f"Error code '{error_code}' not found in locale {requested_locale}, "
                f"falling back to {self._default_locale}"
            )
            messages = self._load_locale(self._default_locale)

        # Return message or empty defaults
        if error_code in messages:
            return messages[error_code]

        logger.warning(f"Error code '{error_code}' not found in any resource file")
        return {"title": "", "detail": ""}
