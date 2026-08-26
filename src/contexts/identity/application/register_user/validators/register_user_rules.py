"""Collect-all-Regeln gegen das public Request-DTO (.rules/python/python-rule-pattern.md).

Die Feldnamen sind die des API-Vertrags (camelCase), weil sie unveraendert im
`errors`-Objekt landen.
"""

from typing import assert_never

from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import (
    DisplayName,
    DisplayNameError,
    DisplayNameIsEmpty,
    DisplayNameRejected,
    DisplayNameTooLong,
    DisplayNameTooShort,
    Email,
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
    IdnEncoder,
    LocaleError,
    LocaleIsEmpty,
    LocaleNotSupported,
    LocaleRejected,
    Password,
    PasswordError,
    PasswordRejected,
    PasswordTooLong,
    PasswordTooShort,
    TimeZoneRejected,
    UnencodableDomainLabel,
    UserCreationError,
    UserTimeZone,
    UserTimeZoneError,
    UserTimeZoneIsEmpty,
    UserTimeZoneUnknown,
    parse_locale,
)
from src.contexts.shared_kernel.validation import FieldError, Rule, all_of

__all__ = ["build_register_user_rules", "to_field_errors"]

_EMAIL = "email"
_PASSWORD = "password"  # noqa: S105 -- Feldname des Vertrags, kein Geheimnis
_DISPLAY_NAME = "displayName"
_LOCALE = "locale"
_TIME_ZONE_ID = "timeZoneId"
"""Die Feldnamen des API-Vertrags - je einmal benannt, weil jeder Arm sie wiederholt.

Sie stehen bewusst als Konstanten und nicht als Literal im Arm: ein umbenanntes
Feld ist eine Vertragsaenderung, und die soll an genau einer Stelle passieren.
"""


def _no_errors(_: object, /) -> list[FieldError]:
    """Der Erfolgs-Arm jeder Regel: ein geparster Wert meldet nichts."""
    return []


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


def email_rule(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Reiche der E-Mail-Regel den IDN-Port per Closure, den sonst keine Regel braucht."""

    def email_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
        """Die E-Mail-Adresse muss wohlgeformt sein."""
        return Email.parse(request.email, idn).fold(_no_errors, _email_errors)

    return email_must_be_wellformed


def password_length_is_in_range(request: RegisterUserRequest) -> list[FieldError]:
    """Das Passwort muss zwischen Mindest- und Hoechstlaenge liegen."""
    return Password.parse(request.password).fold(_no_errors, _password_errors)


def display_name_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
    """Der Anzeigename muss nicht leer, nicht zu kurz und nicht zu lang sein."""
    return DisplayName.parse(request.display_name).fold(_no_errors, _display_name_errors)


def locale_must_be_supported(request: RegisterUserRequest) -> list[FieldError]:
    """Die Sprache muss eine der unterstuetzten sein."""
    return parse_locale(request.locale).fold(_no_errors, _locale_errors)


def time_zone_must_be_known(request: RegisterUserRequest) -> list[FieldError]:
    """Die Zeitzone muss eine bekannte IANA-Id oder ein fester UTC-Versatz sein."""
    return UserTimeZone.parse(request.time_zone_id).fold(_no_errors, _time_zone_errors)


def build_register_user_rules(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Setze das Regelwerk des Use Case zusammen."""
    return all_of(
        email_rule(idn),
        password_length_is_in_range,
        display_name_must_be_wellformed,
        locale_must_be_supported,
        time_zone_must_be_known,
    )


def to_field_errors(rejected: UserCreationError) -> list[FieldError]:
    """Uebersetze eine Ablehnung aus `User.create` in die Feldfehler des Vertrags.

    Die Wurzel parst noch einmal, was das Regelwerk oben schon geprueft hat -
    einmal, um alle Befunde auf einmal zu melden (422), und einmal, weil ein
    `User` nur aus geprueften Werten entstehen darf. Diese Uebersetzung ist
    deshalb im Regelbetrieb unerreichbar.

    Trotzdem uebersetzt und nicht behauptet, sie koenne nicht eintreten: die
    beiden Wege waren schon einmal auseinandergelaufen (`DisplayName`, Vertrag
    gegen Invariante), und ein `AssertionError` an dieser Stelle machte aus einer
    stillen Abweichung einen 500er statt eines ehrlichen 422.

    Die Uebersetzer selbst sind dieselben, die auch das Regelwerk benutzt - der
    Fehlercode eines Falls entsteht damit an genau einer Stelle.
    """
    match rejected:
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
            assert_never(rejected)
