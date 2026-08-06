"""Collect-all-Regeln gegen das public Request-DTO.

Fehlerform entscheidet die Variante: hier fallen viele *unabhaengige* Feldfehler
an, die gemeinsam berichtet werden sollen (`errors.password`, `errors.email`,
... in einer Antwort) - also Collect-all, nicht Fail-fast
(.rules/python/python-rule-pattern.md).

Jede Regel delegiert an die `parse`-Factory des zugehoerigen Value Object und
implementiert die Pruefung damit nicht ein zweites Mal. Die Feldnamen sind die
des API-Vertrags (camelCase), weil sie unveraendert im `errors`-Objekt landen.
"""

from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import (
    DisplayName,
    Email,
    Password,
    UserTimeZone,
    parse_locale,
)
from src.shared_kernel import Err, Ok, Result
from src.shared_kernel.validation import FieldError, Rule, all_of

__all__ = ["register_user_rules"]


def _as_field_errors(field: str, outcome: Result[object, str]) -> list[FieldError]:
    """Uebersetze das Ergebnis einer `parse`-Factory in Feldfehler."""
    match outcome:
        case Ok():
            return []
        case Err(error=message):
            return [FieldError(field, message)]


def email_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
    """Die E-Mail muss sich zu einem `Email`-Value-Object parsen lassen."""
    return _as_field_errors("email", Email.parse(request.email))


def password_must_be_long_enough(request: RegisterUserRequest) -> list[FieldError]:
    """Das Passwort muss die Mindestlaenge erfuellen (BACKEND.md: 400 errors.password)."""
    return _as_field_errors("password", Password.parse(request.password))


def display_name_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
    """Der Anzeigename muss nicht leer und nicht zu lang sein."""
    return _as_field_errors("displayName", DisplayName.parse(request.display_name))


def locale_must_be_supported(request: RegisterUserRequest) -> list[FieldError]:
    """Die Sprache muss eine der unterstuetzten sein."""
    return _as_field_errors("locale", parse_locale(request.locale))


def time_zone_must_be_known(request: RegisterUserRequest) -> list[FieldError]:
    """Die Zeitzone muss eine bekannte IANA-Id sein."""
    return _as_field_errors("timeZoneId", UserTimeZone.parse(request.time_zone_id))


register_user_rules: Rule[RegisterUserRequest] = all_of(
    email_must_be_wellformed,
    password_must_be_long_enough,
    display_name_must_be_wellformed,
    locale_must_be_supported,
    time_zone_must_be_known,
)
