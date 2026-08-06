"""Collect-all-Regeln gegen das public Request-DTO.

Fehlerform entscheidet die Variante: hier fallen viele *unabhaengige* Feldfehler
an, die gemeinsam berichtet werden sollen (`errors.password`, `errors.email`,
... in einer Antwort) - also Collect-all, nicht Fail-fast
(.rules/python/python-rule-pattern.md).

Jede Regel delegiert an die `parse`-Factory des zugehoerigen Value Object und
implementiert die Pruefung damit nicht ein zweites Mal. Die Feldnamen sind die
des API-Vertrags (camelCase), weil sie unveraendert im `errors`-Objekt landen.

Hier - und erst hier - werden Domaenenfehler zu Text fuer Menschen. Die Domaene
sagt, *was* der Fall ist; die Formulierung ist Praesentation.
"""

from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import (
    DisplayName,
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
    Password,
    UnencodableDomainLabel,
    UserTimeZone,
    parse_locale,
)
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import FieldError, Rule, all_of

__all__ = ["build_register_user_rules", "email_message"]


def _as_field_errors(field: str, outcome: Result[object, str]) -> list[FieldError]:
    """Uebersetze das Ergebnis einer `parse`-Factory in Feldfehler."""
    match outcome:
        case Ok():
            return []
        case Err(error=message):
            return [FieldError(field, message)]


def email_message(error: EmailError) -> str:
    """Formuliere den Domaenenfehler einer E-Mail-Adresse fuer Menschen.

    Vollstaendiges Matching ohne Auffangzweig: waechst `EmailError` um einen
    Fall, faellt genau hier auf, dass die Meldung dafuer noch fehlt.
    """
    match error:
        case EmailHasWhitespace():
            return "E-Mail-Adresse darf keinen Leerraum enthalten"
        case EmailNeedsExactlyOneAtSign():
            return "E-Mail-Adresse braucht genau ein '@'"
        case EmailLocalPartMissing():
            return "E-Mail-Adresse braucht einen Teil vor dem '@'"
        case EmailDomainMissing():
            return "E-Mail-Adresse braucht einen Teil hinter dem '@'"
        case EmailLocalPartTooLong(maximum=maximum):
            return f"Teil vor dem '@' darf hoechstens {maximum} Zeichen lang sein"
        case EmailLocalPartHasInvalidCharacters(invalid_characters=invalid):
            return f"unzulaessige Zeichen vor dem '@': {''.join(invalid)!r}"
        case EmailLocalPartHasMisplacedDot():
            return "Punkte vor dem '@' duerfen weder aussen stehen noch doppelt vorkommen"
        case EmailDomainTooLong(maximum=maximum):
            return f"Domain darf hoechstens {maximum} Zeichen lang sein"
        case EmailDomainHasEmptyLabel():
            return "Domain darf kein leeres Label enthalten"
        case EmailDomainLabelTooLong(maximum=maximum):
            return f"Domain-Label darf hoechstens {maximum} Zeichen lang sein"
        case EmailDomainLabelHasEdgeHyphen():
            return "Domain-Label darf nicht mit einem Bindestrich beginnen oder enden"
        case EmailDomainLabelHasInvalidCharacters(label=label):
            return f"unzulaessige Zeichen im Domain-Label: {label!r}"
        case EmailAddressLiteralInvalid(literal=literal):
            return f"kein gueltiges IP-Adress-Literal: {literal!r}"
        case UnencodableDomainLabel(label=label, reason=reason):
            return f"kein gueltiges internationalisiertes Domain-Label: {label!r} ({reason})"


def email_rule(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Regel-Fabrik: die einzige Regel mit einer Abhaengigkeit.

    Die E-Mail-Pruefung braucht den IDN-Port, alle anderen Regeln nicht. Statt
    ihn allen aufzudraengen, bekommt genau diese Regel ihn per Closure.
    """

    def email_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
        return _as_field_errors("email", Email.parse(request.email, idn).map_err(email_message))

    return email_must_be_wellformed


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


def build_register_user_rules(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Setze das Regelwerk des Use Case zusammen."""
    return all_of(
        email_rule(idn),
        password_must_be_long_enough,
        display_name_must_be_wellformed,
        locale_must_be_supported,
        time_zone_must_be_known,
    )
