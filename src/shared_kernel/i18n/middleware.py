"""Accept-Language middleware for content negotiation."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import final

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

ACCEPT_LANGUAGE_HEADER = "Accept-Language"
DEFAULT_LOCALE = "de-DE"


@dataclass(frozen=True, slots=True)
class LocalePreference:
    """Parsed language preference from Accept-Language header.

    Attributes:
        locale: Locale string (e.g., 'de-DE', 'en')
        quality: Quality factor (0.0 to 1.0), default 1.0
    """

    locale: str
    quality: float = 1.0

    def __lt__(self, other: object) -> bool:
        """Compare by quality factor (higher quality sorts first)."""
        if not isinstance(other, LocalePreference):
            return NotImplemented
        # Reverse comparison: higher quality is "less than" (sorts first)
        return self.quality > other.quality


def parse_accept_language_header(header_value: str) -> list[LocalePreference]:
    """Parse Accept-Language header per RFC 7231.

    Examples:
        "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.5"
        -> [LocalePreference('de-DE', 1.0), LocalePreference('de', 0.9), ...]

    Args:
        header_value: Accept-Language header value

    Returns:
        List of LocalePreference objects sorted by quality (descending)
    """
    preferences: list[LocalePreference] = []

    # Split by comma to get individual preferences
    for preference_str in header_value.split(","):
        preference_str = preference_str.strip()
        if not preference_str:
            continue

        # Split locale and quality factor
        parts = preference_str.split(";")
        locale = parts[0].strip()

        quality = 1.0
        if len(parts) > 1:
            # Parse quality factor (e.g., "q=0.9")
            for param in parts[1:]:
                param = param.strip()
                if param.startswith("q="):
                    try:
                        quality = float(param[2:])
                        # Clamp quality to valid range [0, 1]
                        quality = max(0.0, min(1.0, quality))
                    except ValueError:
                        logger.warning(f"Invalid quality value in Accept-Language: {param}")
                        quality = 1.0
                    break

        if locale:
            preferences.append(LocalePreference(locale, quality))

    # Sort by quality (highest first)
    preferences.sort()
    return preferences


@final
class AcceptLanguageMiddleware(BaseHTTPMiddleware):
    """Middleware to extract Accept-Language header and store locale in request state.

    Stores the best-matching locale in request.state.locale for use in
    exception handlers and other downstream handlers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and extract Accept-Language preference.

        Args:
            request: The incoming request
            call_next: The next middleware/handler

        Returns:
            Response with locale stored in request state
        """
        locale = DEFAULT_LOCALE

        # Try to extract Accept-Language header
        if header_value := request.headers.get(ACCEPT_LANGUAGE_HEADER):
            preferences = parse_accept_language_header(header_value)
            if preferences:
                # Use the highest quality preference
                locale = preferences[0].locale
                logger.debug(f"Accept-Language parsed, using locale: {locale}")
        else:
            logger.debug(f"No Accept-Language header, using default locale: {locale}")

        # Normalize locale format: convert single language codes to full locale
        # e.g., "en" -> "en-US", "de" -> "de-DE"
        locale = _normalize_locale(locale)

        # Store in request state for access in exception handlers
        request.state.locale = locale
        logger.debug(f"Locale set in request state: {locale}")

        return await call_next(request)


def _normalize_locale(locale: str) -> str:
    """Normalize locale format to language-REGION.

    Maps language codes to their default regions per RFC 5646.
    If a language code is not mapped, raises ValueError with clear message.

    Supported languages and default regions:
    - 'de' -> 'de-DE', 'en' -> 'en-US', 'fr' -> 'fr-FR', 'es' -> 'es-ES',
    - 'it' -> 'it-IT', 'nl' -> 'nl-NL', 'pt' -> 'pt-PT', 'ru' -> 'ru-RU',
    - 'ja' -> 'ja-JP', 'zh' -> 'zh-CN', 'ko' -> 'ko-KR', 'tr' -> 'tr-TR',
    - 'pl' -> 'pl-PL', 'vi' -> 'vi-VN'

    Args:
        locale: Input locale string (e.g., 'de', 'en-US', 'de-DE')

    Returns:
        Normalized locale string (e.g., 'de-DE', 'en-US')

    Raises:
        ValueError: If language code is not supported.
    """
    # If already in format language-REGION, validate and return as-is
    if len(locale.split("-")) == 2:
        parts = locale.split("-")
        return f"{parts[0].lower()}-{parts[1].upper()}"

    # Map language codes to default regions (RFC 5646 compliant)
    language_to_region = {
        "de": "DE",  # German (Germany)
        "en": "US",  # English (United States)
        "fr": "FR",  # French (France)
        "es": "ES",  # Spanish (Spain)
        "it": "IT",  # Italian (Italy)
        "nl": "NL",  # Dutch (Netherlands)
        "pt": "PT",  # Portuguese (Portugal)
        "ru": "RU",  # Russian (Russia)
        "ja": "JP",  # Japanese (Japan)
        "zh": "CN",  # Chinese (Mainland China)
        "ko": "KR",  # Korean (South Korea)
        "tr": "TR",  # Turkish (Turkey)
        "pl": "PL",  # Polish (Poland)
        "vi": "VN",  # Vietnamese (Vietnam)
    }

    language = locale.split("-")[0].lower()
    if language not in language_to_region:
        raise ValueError(
            f"Unsupported language code: {language!r}. "
            f"Supported languages: {sorted(language_to_region.keys())}"
        )
    region = language_to_region[language]
    return f"{language}-{region}"
