"""Uebersetzt die Ablehnungen der Wurzel in die Feldfehler des API-Vertrags.

Steht hier am Rand und nicht in der Domaene, weil die Feldnamen die des Vertrags
sind (camelCase) - sie landen unveraendert im `errors`-Objekt.
"""

from typing import assert_never

from src.contexts.identity.domain import (
    DisplayNameError,
    DisplayNameIsEmpty,
    DisplayNameRejected,
    DisplayNameTooLong,
    DisplayNameTooShort,
    EmailAddressLiteralInvalid,
    EmailDomainHasEmptyLabel,
    EmailDomainLabelHasEdgeHyphen,
    EmailDomainLabelHasInvalidCharacters,
    EmailDomainLabelTooLong,
    EmailDomainMissing,
    EmailDomainTooLong,
    EmailError,
    EmailHasWhitespace,
    EmailIsEmpty,
    EmailLocalPartHasInvalidCharacters,
    EmailLocalPartHasMisplacedDot,
    EmailLocalPartMissing,
    EmailLocalPartTooLong,
    EmailNeedsExactlyOneAtSign,
    EmailRejected,
    LocaleError,
    LocaleIsEmpty,
    LocaleNotSupported,
    LocaleRejected,
    PasswordError,
    PasswordRejected,
    PasswordTooLong,
    PasswordTooShort,
    TimeZoneRejected,
    UnencodableDomainLabel,
    UserCreationError,
    UserRejected,
    UserTimeZoneError,
    UserTimeZoneIsEmpty,
    UserTimeZoneUnknown,
)
from src.contexts.shared_kernel.validation import FieldError

__all__ = ["to_field_errors"]

_EMAIL = "email"
_PASSWORD = "password"  # noqa: S105 -- Feldname des Vertrags, kein Geheimnis
_DISPLAY_NAME = "displayName"
_LOCALE = "locale"
_TIME_ZONE_ID = "timeZoneId"
"""Die Feldnamen des API-Vertrags - je einmal benannt, weil jeder Arm sie wiederholt.

Sie stehen bewusst als Konstanten und nicht als Literal im Arm: ein umbenanntes
Feld ist eine Vertragsaenderung, und die soll an genau einer Stelle passieren.
"""


def _email_errors(error: EmailError) -> list[FieldError]:  # noqa: C901, PLR0911, PLR0912 -- Exhaustive match over 15+ email error types
    """Uebersetze den Fehler des E-Mail-Parsers in den Feldfehler des Vertrags."""
    match error:
        case EmailIsEmpty():
            return [FieldError(_EMAIL, EmailIsEmpty.code, {})]
        case EmailHasWhitespace():
            return [FieldError(_EMAIL, EmailHasWhitespace.code, {})]
        case EmailNeedsExactlyOneAtSign(at_sign_count=count):
            return [FieldError(_EMAIL, EmailNeedsExactlyOneAtSign.code, {"at_sign_count": count})]
        case EmailLocalPartMissing():
            return [FieldError(_EMAIL, EmailLocalPartMissing.code, {})]
        case EmailDomainMissing():
            return [FieldError(_EMAIL, EmailDomainMissing.code, {})]
        case EmailLocalPartTooLong(maximum=maximum):
            return [FieldError(_EMAIL, EmailLocalPartTooLong.code, {"maximum": maximum})]
        case EmailLocalPartHasInvalidCharacters(invalid_characters=invalid):
            return [
                FieldError(
                    _EMAIL,
                    EmailLocalPartHasInvalidCharacters.code,
                    {"invalid_characters": "".join(invalid)},
                )
            ]
        case EmailLocalPartHasMisplacedDot():
            return [FieldError(_EMAIL, EmailLocalPartHasMisplacedDot.code, {})]
        case EmailDomainTooLong(maximum=maximum):
            return [FieldError(_EMAIL, EmailDomainTooLong.code, {"maximum": maximum})]
        case EmailDomainHasEmptyLabel():
            return [FieldError(_EMAIL, EmailDomainHasEmptyLabel.code, {})]
        case EmailDomainLabelTooLong(maximum=maximum):
            return [FieldError(_EMAIL, EmailDomainLabelTooLong.code, {"maximum": maximum})]
        case EmailDomainLabelHasEdgeHyphen():
            return [FieldError(_EMAIL, EmailDomainLabelHasEdgeHyphen.code, {})]
        case EmailDomainLabelHasInvalidCharacters():
            return [FieldError(_EMAIL, EmailDomainLabelHasInvalidCharacters.code, {})]
        case EmailAddressLiteralInvalid():
            return [FieldError(_EMAIL, EmailAddressLiteralInvalid.code, {})]
        case UnencodableDomainLabel(reason=reason):
            return [FieldError(_EMAIL, UnencodableDomainLabel.code, {"reason": reason})]
        case _:
            assert_never(error)


def _password_errors(error: PasswordError) -> list[FieldError]:
    """Uebersetze den Fehler des Passwort-Parsers in den Feldfehler des Vertrags."""
    match error:
        case PasswordTooShort(actual_length=actual, minimum=minimum):
            return [
                FieldError(
                    _PASSWORD,
                    PasswordTooShort.code,
                    {"actual_length": actual, "minimum": minimum},
                )
            ]
        case PasswordTooLong(actual_length=actual, maximum=maximum):
            return [
                FieldError(
                    _PASSWORD,
                    PasswordTooLong.code,
                    {"actual_length": actual, "maximum": maximum},
                )
            ]
        case _:
            assert_never(error)


def _display_name_errors(error: DisplayNameError) -> list[FieldError]:
    """Uebersetze den Fehler des Anzeigenamen-Parsers in den Feldfehler des Vertrags."""
    match error:
        case DisplayNameIsEmpty():
            return [FieldError(_DISPLAY_NAME, DisplayNameIsEmpty.code, {})]
        case DisplayNameTooShort(actual_length=actual, minimum=minimum):
            return [
                FieldError(
                    _DISPLAY_NAME,
                    DisplayNameTooShort.code,
                    {"actual_length": actual, "minimum": minimum},
                )
            ]
        case DisplayNameTooLong(actual_length=actual, maximum=maximum):
            return [
                FieldError(
                    _DISPLAY_NAME,
                    DisplayNameTooLong.code,
                    {"actual_length": actual, "maximum": maximum},
                )
            ]
        case _:
            assert_never(error)


def _locale_errors(error: LocaleError) -> list[FieldError]:
    """Uebersetze den Fehler des Sprach-Parsers in den Feldfehler des Vertrags."""
    match error:
        case LocaleIsEmpty():
            return [FieldError(_LOCALE, LocaleIsEmpty.code, {})]
        case LocaleNotSupported(candidate=candidate):
            return [FieldError(_LOCALE, LocaleNotSupported.code, {"candidate": candidate})]
        case _:
            assert_never(error)


def _time_zone_errors(error: UserTimeZoneError) -> list[FieldError]:
    """Uebersetze den Fehler des Zeitzonen-Parsers in den Feldfehler des Vertrags."""
    match error:
        case UserTimeZoneIsEmpty():
            return [FieldError(_TIME_ZONE_ID, UserTimeZoneIsEmpty.code, {})]
        case UserTimeZoneUnknown(candidate=candidate):
            return [FieldError(_TIME_ZONE_ID, UserTimeZoneUnknown.code, {"candidate": candidate})]
        case _:
            assert_never(error)


def _rejection_errors(rejection: UserCreationError) -> list[FieldError]:
    """Uebersetze eine einzelne Ablehnung der Wurzel in die Feldfehler des Vertrags."""
    match rejection:
        case EmailRejected(error=error):
            return _email_errors(error)
        case PasswordRejected(error=error):
            return _password_errors(error)
        case DisplayNameRejected(error=error):
            return _display_name_errors(error)
        case LocaleRejected(error=error):
            return _locale_errors(error)
        case TimeZoneRejected(error=error):
            return _time_zone_errors(error)
        case _:
            assert_never(rejection)


def to_field_errors(rejected: UserRejected) -> list[FieldError]:
    """Uebersetze **alle** Befunde aus `User.create` in die Feldfehler des Vertrags.

    Der einzige Weg, auf dem ein 422 entsteht.
    """
    return [error for rejection in rejected.rejections for error in _rejection_errors(rejection)]
