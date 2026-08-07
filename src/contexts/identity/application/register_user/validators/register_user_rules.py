"""Collect-all-Regeln gegen das public Request-DTO.

Fehlerform entscheidet die Variante: hier fallen viele *unabhaengige* Feldfehler
an, die gemeinsam berichtet werden sollen (`errors.password`, `errors.email`,
... in einer Antwort) - also Collect-all, nicht Fail-fast
(.rules/python/python-rule-pattern.md).

**Eine Regel ist eine Funktion mit der Signatur `Rule[RegisterUserRequest]`, die
genau eine Frage beantwortet** - und sie beantwortet sie selbst. Kein
generischer Helfer mit Konverter-Callback dazwischen: der musste seine Signatur
ueber fuenf verschiedene Fehlertypen spannen und wurde dabei erst zu
`Result[object, Exception]` aufgemacht und dann unwahr, denn diese Fehlerfaelle
sind frozen Dataclasses und keine `Exception`. Steht die Fallunterscheidung in
der Regel, bleibt der konkrete Typ erhalten und die Annotation stimmt.

Jede Regel delegiert die Pruefung selbst an die `parse`-Factory ihres Value
Object und implementiert sie damit nicht ein zweites Mal. Die Feldnamen sind die
des API-Vertrags (camelCase), weil sie unveraendert im `errors`-Objekt landen.

Domaenenfehler werden hier in sprachunabhaengige Codes + Parameter uebersetzt,
nicht in Text fuer Menschen. Der Text entsteht erst am HTTP-Rand nach
`Accept-Language`.
"""

from typing import assert_never

from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import (
    DisplayName,
    DisplayNameIsEmpty,
    DisplayNameTooLong,
    Email,
    EmailAddressLiteralInvalid,
    EmailDomainHasEmptyLabel,
    EmailDomainLabelHasEdgeHyphen,
    EmailDomainLabelHasInvalidCharacters,
    EmailDomainLabelTooLong,
    EmailDomainMissing,
    EmailDomainTooLong,
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
    UnencodableDomainLabel,
    UserTimeZone,
    UserTimeZoneUnknown,
    parse_locale,
)
from src.contexts.shared_kernel import Err, Ok
from src.contexts.shared_kernel.validation import FieldError, Rule, all_of

__all__ = ["build_register_user_rules"]

_EMAIL = "email"
"""Feldname des API-Vertrags - als Konstante, weil ihn vierzehn Arme wiederholen.

Die uebrigen Regeln haben je einen Arm und nennen ihren Feldnamen dort direkt:
eine Konstante fuer eine einzige Verwendungsstelle verschiebt die Antwort nur
eine Zeile weiter nach oben.
"""


def email_rule(idn: IdnEncoder) -> Rule[RegisterUserRequest]:  # noqa: C901 -- Closure factory for dependency injection
    """Regel-Fabrik: die einzige Regel mit einer Abhaengigkeit.

    Die E-Mail-Pruefung braucht den IDN-Port, alle anderen Regeln nicht. Statt
    ihn allen aufzudraengen, bekommt genau diese Regel ihn per Closure.
    """

    def email_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:  # noqa: C901, PLR0911, PLR0912 -- Exhaustive match over 15+ email error types
        """Die E-Mail-Adresse muss wohlgeformt sein.

        Vierzehn Arme, einer je Regel aus `Email.parse` - das ist der Preis
        dafuer, dass die Domaene die Adresse nicht per Regex, sondern in einzeln
        benannten Faellen prueft. Jeder Fall hat einen eigenen Code und eine
        eigene Textvorlage; sie zusammenzufassen hiesse, dem Aufrufer statt der
        Ursache nur noch "ungueltig" zu sagen.
        """
        outcome = Email.parse(request.email, idn)
        match outcome:
            case Ok():
                return []
            case Err(error=EmailHasWhitespace()):
                return [FieldError(_EMAIL, EmailHasWhitespace.code, {})]
            case Err(error=EmailNeedsExactlyOneAtSign(at_sign_count=count)):
                return [
                    FieldError(
                        _EMAIL,
                        EmailNeedsExactlyOneAtSign.code,
                        {"at_sign_count": count},
                    )
                ]
            case Err(error=EmailLocalPartMissing()):
                return [FieldError(_EMAIL, EmailLocalPartMissing.code, {})]
            case Err(error=EmailDomainMissing()):
                return [FieldError(_EMAIL, EmailDomainMissing.code, {})]
            case Err(error=EmailLocalPartTooLong(maximum=maximum)):
                return [FieldError(_EMAIL, EmailLocalPartTooLong.code, {"maximum": maximum})]
            case Err(error=EmailLocalPartHasInvalidCharacters(invalid_characters=invalid)):
                return [
                    FieldError(
                        _EMAIL,
                        EmailLocalPartHasInvalidCharacters.code,
                        {"invalid_characters": "".join(invalid)},
                    )
                ]
            case Err(error=EmailLocalPartHasMisplacedDot()):
                return [FieldError(_EMAIL, EmailLocalPartHasMisplacedDot.code, {})]
            case Err(error=EmailDomainTooLong(maximum=maximum)):
                return [FieldError(_EMAIL, EmailDomainTooLong.code, {"maximum": maximum})]
            case Err(error=EmailDomainHasEmptyLabel()):
                return [FieldError(_EMAIL, EmailDomainHasEmptyLabel.code, {})]
            case Err(error=EmailDomainLabelTooLong(maximum=maximum)):
                return [FieldError(_EMAIL, EmailDomainLabelTooLong.code, {"maximum": maximum})]
            case Err(error=EmailDomainLabelHasEdgeHyphen()):
                return [FieldError(_EMAIL, EmailDomainLabelHasEdgeHyphen.code, {})]
            case Err(error=EmailDomainLabelHasInvalidCharacters()):
                return [FieldError(_EMAIL, EmailDomainLabelHasInvalidCharacters.code, {})]
            case Err(error=EmailAddressLiteralInvalid()):
                return [FieldError(_EMAIL, EmailAddressLiteralInvalid.code, {})]
            case Err(error=UnencodableDomainLabel(reason=reason)):
                return [FieldError(_EMAIL, UnencodableDomainLabel.code, {"reason": reason})]
            case _:
                assert_never(outcome)

    return email_must_be_wellformed


def password_must_be_long_enough(request: RegisterUserRequest) -> list[FieldError]:
    """Das Passwort muss die Mindestlaenge erfuellen."""
    outcome = Password.parse(request.password)
    match outcome:
        case Ok():
            return []
        case Err(error=PasswordTooShort(actual_length=actual, minimum=minimum)):
            return [
                FieldError(
                    "password",
                    PasswordTooShort.code,
                    {"actual_length": actual, "minimum": minimum},
                )
            ]
        case _:
            assert_never(outcome)


def display_name_must_be_wellformed(request: RegisterUserRequest) -> list[FieldError]:
    """Der Anzeigename muss nicht leer und nicht zu lang sein."""
    outcome = DisplayName.parse(request.display_name)
    match outcome:
        case Ok():
            return []
        case Err(error=DisplayNameIsEmpty()):
            return [FieldError("displayName", DisplayNameIsEmpty.code, {})]
        case Err(error=DisplayNameTooLong(actual_length=actual, maximum=maximum)):
            return [
                FieldError(
                    "displayName",
                    DisplayNameTooLong.code,
                    {"actual_length": actual, "maximum": maximum},
                )
            ]
        case _:
            assert_never(outcome)


def locale_must_be_supported(request: RegisterUserRequest) -> list[FieldError]:
    """Die Sprache muss eine der unterstuetzten sein."""
    outcome = parse_locale(request.locale)
    match outcome:
        case Ok():
            return []
        case Err(error=LocaleNotSupported(candidate=candidate)):
            return [FieldError("locale", LocaleNotSupported.code, {"candidate": candidate})]
        case _:
            assert_never(outcome)


def time_zone_must_be_known(request: RegisterUserRequest) -> list[FieldError]:
    """Die Zeitzone muss eine bekannte IANA-Id sein."""
    outcome = UserTimeZone.parse(request.time_zone_id)
    match outcome:
        case Ok():
            return []
        case Err(error=UserTimeZoneUnknown(candidate=candidate)):
            return [FieldError("timeZoneId", UserTimeZoneUnknown.code, {"candidate": candidate})]
        case _:
            assert_never(outcome)


def build_register_user_rules(idn: IdnEncoder) -> Rule[RegisterUserRequest]:
    """Setze das Regelwerk des Use Case zusammen."""
    return all_of(
        email_rule(idn),
        password_must_be_long_enough,
        display_name_must_be_wellformed,
        locale_must_be_supported,
        time_zone_must_be_known,
    )
