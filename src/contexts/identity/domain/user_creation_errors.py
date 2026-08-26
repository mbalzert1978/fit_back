"""Was beim Bau der Aggregatwurzel `User` schiefgehen kann - je Feld ein Fall.

Warum die Fehler der Parser hier noch einmal eingepackt werden, statt sie flach
zu vereinigen: `EmailIsEmpty | PasswordTooShort | ...` verloere, **zu welchem
Feld** ein Fall gehoert. Wer den Fehler spaeter auf einen Feldfehler des Vertrags
abbildet, muesste die Zugehoerigkeit aus dem Klassennamen erraten und einen
`match` ueber zwei Dutzend Faelle schreiben.

So sind es fuenf Faelle, einer je Feld, und der `match` darueber ist wieder eine
Aussage statt einer Pflichtuebung (.rules/python/python-feature-slices.md).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain.display_name_errors import DisplayNameError
from src.contexts.identity.domain.email_errors import EmailError
from src.contexts.identity.domain.locale_errors import LocaleError
from src.contexts.identity.domain.password_errors import PasswordError
from src.contexts.identity.domain.user_time_zone_errors import UserTimeZoneError

__all__ = [
    "DisplayNameRejected",
    "EmailRejected",
    "LocaleRejected",
    "PasswordRejected",
    "TimeZoneRejected",
    "UserCreationError",
    "UserRejected",
    "display_name_rejection",
    "email_rejection",
    "locale_rejection",
    "password_rejection",
    "time_zone_rejection",
    "user_rejected",
]


@final
@dataclass(frozen=True, slots=True)
class EmailRejected:
    """Die E-Mail-Adresse hat ihre Regeln nicht bestanden."""

    error: EmailError


@final
@dataclass(frozen=True, slots=True)
class PasswordRejected:
    """Das Passwort hat seine Regeln nicht bestanden."""

    error: PasswordError


@final
@dataclass(frozen=True, slots=True)
class DisplayNameRejected:
    """Der Anzeigename hat seine Regeln nicht bestanden."""

    error: DisplayNameError


@final
@dataclass(frozen=True, slots=True)
class LocaleRejected:
    """Die Sprach-Kennung hat ihre Regeln nicht bestanden."""

    error: LocaleError


@final
@dataclass(frozen=True, slots=True)
class TimeZoneRejected:
    """Die Zeitzonen-Angabe hat ihre Regeln nicht bestanden."""

    error: UserTimeZoneError


type UserCreationError = (
    EmailRejected | PasswordRejected | DisplayNameRejected | LocaleRejected | TimeZoneRejected
)
"""Die **erwarteten** Ausgaenge von `User.create` - genau die fuenf Felder.

Kommt ein Feld zur Wurzel dazu, erzwingt das eine Aenderung an dieser Zeile und
damit an jedem `match` darueber.
"""


@final
@dataclass(frozen=True, slots=True)
class UserRejected:
    """Die Wurzel ist nicht entstanden - hier stehen **alle** Gruende, nicht der erste.

    Ein eigener Fall und keine nackte Liste: `case list()` neben
    `case EmailAlreadyRegistered()` waere eine Aussage ueber die Datenstruktur
    statt ueber die Fachlichkeit.
    """

    rejections: tuple[UserCreationError, ...]


def user_rejected(rejections: Sequence[UserCreationError]) -> UserRejected:
    """Fasse die gesammelten Ablehnungen zum einen Fehler von `User.create` zusammen."""
    return UserRejected(tuple(rejections))


def email_rejection(error: EmailError) -> list[UserCreationError]:
    """Hebe den E-Mail-Fehler in die Sammelform der Kette."""
    return [EmailRejected(error)]


def password_rejection(error: PasswordError) -> list[UserCreationError]:
    """Hebe den Passwort-Fehler in die Sammelform der Kette."""
    return [PasswordRejected(error)]


def display_name_rejection(error: DisplayNameError) -> list[UserCreationError]:
    """Hebe den Anzeigenamen-Fehler in die Sammelform der Kette."""
    return [DisplayNameRejected(error)]


def locale_rejection(error: LocaleError) -> list[UserCreationError]:
    """Hebe den Sprach-Fehler in die Sammelform der Kette."""
    return [LocaleRejected(error)]


def time_zone_rejection(error: UserTimeZoneError) -> list[UserCreationError]:
    """Hebe den Zeitzonen-Fehler in die Sammelform der Kette."""
    return [TimeZoneRejected(error)]
