"""Collect-all-Regeln gegen das public Request-DTO.

Fehlerform entscheidet die Variante: hier fallen viele *unabhaengige* Feldfehler
an, die gemeinsam berichtet werden sollen (`errors.password`, `errors.email`,
... in einer Antwort) - also Collect-all, nicht Fail-fast
(.rules/python/python-rule-pattern.md).

Jede Regel delegiert an die `parse`-Factory des zugehoerigen Value Object und
implementiert die Pruefung damit nicht ein zweites Mal. Die Feldnamen sind die
des API-Vertrags (camelCase), weil sie unveraendert im `errors`-Objekt landen.

Domaenenfehler werden hier in sprachunabhaengige Codes + Parameter uebersetzt,
nicht in Text fuer Menschen. Der Text entsteht erst am HTTP-Rand nach `Accept-Language`.
"""

from collections.abc import Callable, Mapping

from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import (
    DisplayName,
    DisplayNameTooLong,
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
    EmailLocalPartHasInvalidCharacters,
    EmailLocalPartHasMisplacedDot,
    EmailLocalPartMissing,
    EmailLocalPartTooLong,
    EmailNeedsExactlyOneAtSign,
    IdnEncoder,
    LocaleNotSupported,
    Password,
    PasswordTooShort,
    TextIsEmpty,
    UnencodableDomainLabel,
    UserTimeZone,
    UserTimeZoneUnknown,
    parse_locale,
)
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import FieldError, Rule, all_of

__all__ = ["build_register_user_rules"]


def _as_field_errors_from_email(
    field: str, outcome: Result[object, EmailError]
) -> list[FieldError]:
    """Uebersetze einen EmailError in Feldfehler mit Code + Parametern."""
    match outcome:
        case Ok():
            return []
        case Err(error=email_error):
            code, params = _email_error_to_code_params(email_error)
            return [FieldError(field, code, params)]


def _email_error_to_code_params(error: EmailError) -> tuple[str, Mapping[str, object]]:
    """Konvertiere einen EmailError in (code, parameters) fuer die Ressource-Datei."""
    match error:
        case EmailHasWhitespace():
            return ("email-has-whitespace", {})
        case EmailNeedsExactlyOneAtSign(at_sign_count=count):
            return ("email-needs-exactly-one-at-sign", {"count": count})
        case EmailLocalPartMissing():
            return ("email-local-part-missing", {})
        case EmailDomainMissing():
            return ("email-domain-missing", {})
        case EmailLocalPartTooLong(maximum=maximum):
            return ("email-local-part-too-long", {"maximum": maximum})
        case EmailLocalPartHasInvalidCharacters(invalid_characters=invalid):
            return ("email-local-part-has-invalid-characters", {"invalid": "".join(invalid)})
        case EmailLocalPartHasMisplacedDot():
            return ("email-local-part-has-misplaced-dot", {})
        case EmailDomainTooLong(maximum=maximum):
            return ("email-domain-too-long", {"maximum": maximum})
        case EmailDomainHasEmptyLabel():
            return ("email-domain-has-empty-label", {})
        case EmailDomainLabelTooLong(maximum=maximum):
            return ("email-domain-label-too-long", {"maximum": maximum})
        case EmailDomainLabelHasEdgeHyphen():
            return ("email-domain-label-has-edge-hyphen", {})
        case EmailDomainLabelHasInvalidCharacters():
            return ("email-domain-label-has-invalid-characters", {})
        case EmailAddressLiteralInvalid():
            return ("email-address-literal-invalid", {})
        case UnencodableDomainLabel(reason=reason):
            return ("email-unencodable-domain-label", {"reason": reason})


def _password_error_to_code_params(error: Exception) -> tuple[str, Mapping[str, object]]:
    """Konvertiere einen PasswordError in (code, parameters)."""
    match error:
        case PasswordTooShort(actual_length=actual, minimum=minimum):
            return ("password-too-short", {"actual_length": actual, "minimum": minimum})


def _display_name_error_to_code_params(error: Exception) -> tuple[str, Mapping[str, object]]:
    """Konvertiere einen DisplayNameError in (code, parameters)."""
    match error:
        case TextIsEmpty():
            return ("display-name-is-empty", {})
        case DisplayNameTooLong(actual_length=actual, maximum=maximum):
            return ("display-name-too-long", {"actual_length": actual, "maximum": maximum})


def _locale_error_to_code_params(error: Exception) -> tuple[str, Mapping[str, object]]:
    """Konvertiere einen LocaleError in (code, parameters)."""
    match error:
        case LocaleNotSupported(candidate=candidate):
            return ("locale-not-supported", {"candidate": candidate})


def _user_time_zone_error_to_code_params(error: Exception) -> tuple[str, Mapping[str, object]]:
    """Konvertiere einen UserTimeZoneError in (code, parameters)."""
    match error:
        case UserTimeZoneUnknown(candidate=candidate):
            return ("user-time-zone-unknown", {"candidate": candidate})


def _as_field_errors_generic(
    field: str,
    outcome: Result[object, Exception],
    converter: Callable[[Exception], tuple[str, Mapping[str, object]]],
) -> list[FieldError]:
    """Uebersetze einen typisierten Fehler in Feldfehler mit Code + Parametern.

    `converter` ist eine Funktion, die den Error-Typ in (code, parameters) umwandelt.
    """
    match outcome:
        case Ok():
            return []
        case Err(error=error):
            code, params = converter(error)
            return [FieldError(field, code, params)]


def email_rule(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Regel-Fabrik: die einzige Regel mit einer Abhaengigkeit.

    Die E-Mail-Pruefung braucht den IDN-Port, alle anderen Regeln nicht. Statt
    ihn allen aufzudraengen, bekommt genau diese Regel ihn per Closure.
    """

    def email_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
        return _as_field_errors_from_email("email", Email.parse(request.email, idn))

    return email_must_be_wellformed


def password_must_be_long_enough(request: RegisterUserRequest) -> list[FieldError]:
    """Das Passwort muss die Mindestlaenge erfuellen."""
    return _as_field_errors_generic(
        "password", Password.parse(request.password), _password_error_to_code_params
    )


def display_name_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
    """Der Anzeigename muss nicht leer und nicht zu lang sein."""
    return _as_field_errors_generic(
        "displayName", DisplayName.parse(request.display_name), _display_name_error_to_code_params
    )


def locale_must_be_supported(request: RegisterUserRequest) -> list[FieldError]:
    """Die Sprache muss eine der unterstuetzten sein."""
    return _as_field_errors_generic(
        "locale", parse_locale(request.locale), _locale_error_to_code_params
    )


def time_zone_must_be_known(request: RegisterUserRequest) -> list[FieldError]:
    """Die Zeitzone muss eine bekannte IANA-Id sein."""
    return _as_field_errors_generic(
        "timeZoneId", UserTimeZone.parse(request.time_zone_id), _user_time_zone_error_to_code_params
    )


def build_register_user_rules(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Setze das Regelwerk des Use Case zusammen."""
    return all_of(
        email_rule(idn),
        password_must_be_long_enough,
        display_name_must_be_wellformed,
        locale_must_be_supported,
        time_zone_must_be_known,
    )
