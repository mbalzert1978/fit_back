"""Collect-all-Regeln gegen das public Request-DTO (.rules/python/python-rule-pattern.md).

Die Feldnamen sind die des API-Vertrags (camelCase), weil sie unveraendert im
`errors`-Objekt landen.
"""

from typing import assert_never

from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import (
    DisplayName,
    DisplayNameIsEmpty,
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
    EmailHasWhitespace,
    EmailIsEmpty,
    EmailLocalPartHasInvalidCharacters,
    EmailLocalPartHasMisplacedDot,
    EmailLocalPartMissing,
    EmailLocalPartTooLong,
    EmailNeedsExactlyOneAtSign,
    IdnEncoder,
    LocaleIsEmpty,
    LocaleNotSupported,
    Password,
    PasswordTooLong,
    PasswordTooShort,
    UnencodableDomainLabel,
    UserTimeZone,
    UserTimeZoneIsEmpty,
    UserTimeZoneUnknown,
    parse_locale,
)
from src.contexts.shared_kernel import Err, Ok
from src.contexts.shared_kernel.validation import FieldError, Rule, all_of

__all__ = ["build_register_user_rules"]

_EMAIL = "email"
"""Feldname des API-Vertrags - als Konstante, weil ihn fuenfzehn Arme wiederholen."""


def email_rule(idn: IdnEncoder) -> Rule[RegisterUserRequest]:  # noqa: C901 -- Closure factory for dependency injection
    """Reiche der E-Mail-Regel den IDN-Port per Closure, den sonst keine Regel braucht."""

    def email_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:  # noqa: C901, PLR0911, PLR0912 -- Exhaustive match over 15+ email error types
        """Die E-Mail-Adresse muss wohlgeformt sein."""
        outcome = Email.parse(request.email, idn)
        match outcome:
            case Ok():
                return []
            case Err(error=error):
                match error:
                    case EmailIsEmpty():
                        return [FieldError(_EMAIL, EmailIsEmpty.code, {})]
                    case EmailHasWhitespace():
                        return [FieldError(_EMAIL, EmailHasWhitespace.code, {})]
                    case EmailNeedsExactlyOneAtSign(at_sign_count=count):
                        return [
                            FieldError(
                                _EMAIL,
                                EmailNeedsExactlyOneAtSign.code,
                                {"at_sign_count": count},
                            )
                        ]
                    case EmailLocalPartMissing():
                        return [FieldError(_EMAIL, EmailLocalPartMissing.code, {})]
                    case EmailDomainMissing():
                        return [FieldError(_EMAIL, EmailDomainMissing.code, {})]
                    case EmailLocalPartTooLong(maximum=maximum):
                        return [
                            FieldError(_EMAIL, EmailLocalPartTooLong.code, {"maximum": maximum})
                        ]
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
                        return [
                            FieldError(_EMAIL, EmailDomainLabelTooLong.code, {"maximum": maximum})
                        ]
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
            case _:
                assert_never(outcome)

    return email_must_be_wellformed


def password_length_is_in_range(request: RegisterUserRequest) -> list[FieldError]:
    """Das Passwort muss zwischen Mindest- und Hoechstlaenge liegen."""
    outcome = Password.parse(request.password)
    match outcome:
        case Ok():
            return []
        case Err(error=error):
            match error:
                case PasswordTooShort(actual_length=actual, minimum=minimum):
                    return [
                        FieldError(
                            "password",
                            PasswordTooShort.code,
                            {"actual_length": actual, "minimum": minimum},
                        )
                    ]
                case PasswordTooLong(actual_length=actual, maximum=maximum):
                    return [
                        FieldError(
                            "password",
                            PasswordTooLong.code,
                            {"actual_length": actual, "maximum": maximum},
                        )
                    ]
                case _:
                    assert_never(error)
        case _:
            assert_never(outcome)


def display_name_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
    """Der Anzeigename muss nicht leer, nicht zu kurz und nicht zu lang sein."""
    outcome = DisplayName.parse(request.display_name)
    match outcome:
        case Ok():
            return []
        case Err(error=error):
            match error:
                case DisplayNameIsEmpty():
                    return [FieldError("displayName", DisplayNameIsEmpty.code, {})]
                case DisplayNameTooShort(actual_length=actual, minimum=minimum):
                    return [
                        FieldError(
                            "displayName",
                            DisplayNameTooShort.code,
                            {"actual_length": actual, "minimum": minimum},
                        )
                    ]
                case DisplayNameTooLong(actual_length=actual, maximum=maximum):
                    return [
                        FieldError(
                            "displayName",
                            DisplayNameTooLong.code,
                            {"actual_length": actual, "maximum": maximum},
                        )
                    ]
                case _:
                    assert_never(error)
        case _:
            assert_never(outcome)


def locale_must_be_supported(request: RegisterUserRequest) -> list[FieldError]:
    """Die Sprache muss eine der unterstuetzten sein."""
    outcome = parse_locale(request.locale)
    match outcome:
        case Ok():
            return []
        case Err(error=error):
            match error:
                case LocaleIsEmpty():
                    return [FieldError("locale", LocaleIsEmpty.code, {})]
                case LocaleNotSupported(candidate=candidate):
                    return [FieldError("locale", LocaleNotSupported.code, {"candidate": candidate})]
                case _:
                    assert_never(error)
        case _:
            assert_never(outcome)


def time_zone_must_be_known(request: RegisterUserRequest) -> list[FieldError]:
    """Die Zeitzone muss eine bekannte IANA-Id oder ein fester UTC-Versatz sein."""
    outcome = UserTimeZone.parse(request.time_zone_id)
    match outcome:
        case Ok():
            return []
        case Err(error=error):
            match error:
                case UserTimeZoneIsEmpty():
                    return [FieldError("timeZoneId", UserTimeZoneIsEmpty.code, {})]
                case UserTimeZoneUnknown(candidate=candidate):
                    return [
                        FieldError(
                            "timeZoneId",
                            UserTimeZoneUnknown.code,
                            {"candidate": candidate},
                        )
                    ]
                case _:
                    assert_never(error)
        case _:
            assert_never(outcome)


def build_register_user_rules(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Setze das Regelwerk des Use Case zusammen."""
    return all_of(
        email_rule(idn),
        password_length_is_in_range,
        display_name_must_be_wellformed,
        locale_must_be_supported,
        time_zone_must_be_known,
    )
