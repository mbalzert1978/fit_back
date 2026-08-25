"""Tagged Union Locale - die vom Backend unterstuetzten Sprachen, kein Enum."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import assert_never, final

from src.contexts.identity.domain.locale_errors import (
    LocaleError,
    LocaleIsEmpty,
    LocaleNotSupported,
)
from src.contexts.shared_kernel import Err, Ok, Result, not_blank_as
from src.contexts.shared_kernel.validation import ParseRule, ResultRule

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


is_not_blank: ResultRule[str, LocaleError] = not_blank_as(LocaleIsEmpty)
"""Die Kennung besteht nicht nur aus Leerraum - und kommt getrimmt zurueck."""


def is_supported_tag(candidate: str) -> Result[Locale, LocaleError]:
    """Die Kennung steht in der Tabelle der unterstuetzten Sprachen.

    Der Tabellentreffer *ist* die Sprache - deshalb `ParseRule`.
    """
    if (locale := _BY_TAG.get(candidate.casefold())) is None:
        return Err(LocaleNotSupported(candidate))
    return Ok(locale)


_RULE: ParseRule[str, Locale, LocaleError] = is_supported_tag


def parse_locale(raw: str) -> Result[Locale, LocaleError]:
    """Lies eine moeglicherweise nicht unterstuetzte Sprach-Kennung.

    `bind` statt `chain`: die beiden Regeln haben verschiedene Ausgangsformen.
    """
    return is_not_blank(raw).bind(_RULE)


def hydrate_locale(raw: str) -> Locale:
    """Rekonstruiere aus einem bereits validierten Rohwert."""
    match parse_locale(raw):
        case Ok(value=locale):
            return locale
        case Err():
            msg = f"unreachable: {raw!r} wurde vorgelagert validiert"
            raise AssertionError(msg)


def locale_tag(locale: Locale) -> str:
    """Bilde die Sprache auf ihre Kennung ab - nur an Protokoll-/Persistenzgrenzen."""
    match locale:
        case German():
            return "de"
        case English():
            return "en"
        case _:
            assert_never(locale)
