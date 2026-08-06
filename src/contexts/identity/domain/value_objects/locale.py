"""Tagged Union Locale - die vom Backend unterstuetzten Sprachen, kein Enum."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from src.shared_kernel import Err, Ok, Result

__all__ = [
    "DEFAULT_LOCALE",
    "English",
    "German",
    "Locale",
    "hydrate_locale",
    "locale_tag",
    "parse_locale",
]


@final
@dataclass(frozen=True, slots=True)
class German:
    """Deutsch (de) - Default laut BACKEND.md Abschnitt 1."""


@final
@dataclass(frozen=True, slots=True)
class English:
    """Englisch (en)."""


type Locale = German | English

DEFAULT_LOCALE: Locale = German()

_BY_TAG: Mapping[str, Locale] = {"de": German(), "en": English()}


def parse_locale(raw: str) -> Result[Locale, str]:
    """Lies eine moeglicherweise nicht unterstuetzte Sprach-Kennung."""
    if (locale := _BY_TAG.get(raw.strip().casefold())) is None:
        return Err(f"nicht unterstuetzte Sprache: {raw!r}")
    return Ok(locale)


def hydrate_locale(raw: str) -> Locale:
    """Rekonstruiere aus einem bereits validierten Rohwert."""
    match parse_locale(raw):
        case Ok(value=locale):
            return locale
        case Err():
            raise AssertionError(f"unreachable: {raw!r} wurde vorgelagert validiert")


def locale_tag(locale: Locale) -> str:
    """Bilde die Sprache auf ihre Kennung ab - nur an Protokoll-/Persistenzgrenzen."""
    match locale:
        case German():
            return "de"
        case English():
            return "en"
