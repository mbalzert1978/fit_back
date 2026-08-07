"""Response-Mapper: Ergebnis -> public Response-Union. Eine Richtung, kein Hinweg."""

from collections.abc import Iterable, Mapping

from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import (
    DomainError,
    DisplayNameTooLong,
    EmailAlreadyRegistered,
    LocaleNotSupported,
    PasswordHashIsEmpty,
    PasswordTooShort,
    TextIsEmpty,
    User,
    UserIdMalformed,
    UserTimeZoneUnknown,
    locale_tag,
)
from src.contexts.identity.domain.email_errors import (
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
    UnencodableDomainLabel,
)
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import FieldError, FieldErrorDetail, group_by_field

__all__ = ["to_invalid_response", "to_response"]


def _email_error_to_code_params(error: EmailError) -> tuple[str, Mapping[str, object]]:
    """Konvertiere einen EmailError in (code, parameters)."""
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


def to_response(outcome: Result[User, DomainError]) -> RegisterUserResponse:
    """Uebersetze den Domaenen-Ausgang in die public Antwort.

    Hier wird gematcht statt `map`/`bind` verkettet, und das ist Absicht: aus
    `Result[User, DomainError]` werden zwei **verschiedene** Response-Typen. Das
    ist ein Fold aus dem `Result` heraus, keine Transformation darin - `map`
    kaeme nie aus dem Ok-Zweig heraus.

    Vollstaendiges Matching ohne Auffangzweig: waechst `DomainError` um einen
    Fall, faellt genau hier auf, dass die Antwort dafuer noch fehlt.

    HINWEIS: Domain-Fehler aus den Value-Object-Parsern (z.B. Email, Password,
    DisplayName) sollten hier nicht ankommen - die Request-Validierung faengt sie
    alle auf und gibt `to_invalid_response()` zurueck. Nur `EmailAlreadyRegistered`
    vom Port ist erwartet. Die Faelle unten sind der Vollstaendigkeit halber da,
    wuerde aber auf unerwartete Fehler hindeuten.
    """
    match outcome:
        case Ok(value=user):
            return RegistrationAccepted(
                user_id=str(user.id),
                email=user.email.value,
                display_name=user.display_name.text,
                locale=locale_tag(user.locale),
                time_zone_id=user.time_zone.value,
                registered_at_unix=user.registered_at.unix_seconds,
            )
        case Err(error=EmailAlreadyRegistered(email=email)):
            return EmailAlreadyTaken(email.value)
        case Err(error=EmailHasWhitespace()):
            code, params = ("email-has-whitespace", {})
            return _to_invalid_field_response("email", code, params)
        case Err(error=EmailNeedsExactlyOneAtSign(at_sign_count=count)):
            return _to_invalid_field_response("email", "email-needs-exactly-one-at-sign", {"count": count})
        case Err(error=EmailLocalPartMissing()):
            return _to_invalid_field_response("email", "email-local-part-missing", {})
        case Err(error=EmailDomainMissing()):
            return _to_invalid_field_response("email", "email-domain-missing", {})
        case Err(error=EmailLocalPartTooLong(maximum=maximum)):
            return _to_invalid_field_response("email", "email-local-part-too-long", {"maximum": maximum})
        case Err(error=EmailLocalPartHasInvalidCharacters(invalid_characters=invalid)):
            return _to_invalid_field_response("email", "email-local-part-has-invalid-characters", {"invalid": "".join(invalid)})
        case Err(error=EmailLocalPartHasMisplacedDot()):
            return _to_invalid_field_response("email", "email-local-part-has-misplaced-dot", {})
        case Err(error=EmailDomainTooLong(maximum=maximum)):
            return _to_invalid_field_response("email", "email-domain-too-long", {"maximum": maximum})
        case Err(error=EmailDomainHasEmptyLabel()):
            return _to_invalid_field_response("email", "email-domain-has-empty-label", {})
        case Err(error=EmailDomainLabelTooLong(maximum=maximum)):
            return _to_invalid_field_response("email", "email-domain-label-too-long", {"maximum": maximum})
        case Err(error=EmailDomainLabelHasEdgeHyphen()):
            return _to_invalid_field_response("email", "email-domain-label-has-edge-hyphen", {})
        case Err(error=EmailDomainLabelHasInvalidCharacters()):
            return _to_invalid_field_response("email", "email-domain-label-has-invalid-characters", {})
        case Err(error=EmailAddressLiteralInvalid()):
            return _to_invalid_field_response("email", "email-address-literal-invalid", {})
        case Err(error=UnencodableDomainLabel(reason=reason)):
            return _to_invalid_field_response("email", "email-unencodable-domain-label", {"reason": reason})
        case Err(error=PasswordTooShort(actual_length=actual, minimum=minimum)):
            return _to_invalid_field_response("password", "password-too-short", {"actual_length": actual, "minimum": minimum})
        case Err(error=TextIsEmpty()):
            return _to_invalid_field_response("displayName", "display-name-is-empty", {})
        case Err(error=DisplayNameTooLong(actual_length=actual, maximum=maximum)):
            return _to_invalid_field_response("displayName", "display-name-too-long", {"actual_length": actual, "maximum": maximum})
        case Err(error=LocaleNotSupported(candidate=candidate)):
            return _to_invalid_field_response("locale", "locale-not-supported", {"candidate": candidate})
        case Err(error=PasswordHashIsEmpty()):
            raise RuntimeError("Password hash creation failed unexpectedly")
        case Err(error=UserIdMalformed(candidate=candidate)):
            raise RuntimeError(f"User ID generation failed: {candidate}")
        case Err(error=UserTimeZoneUnknown(candidate=candidate)):
            return _to_invalid_field_response("timeZoneId", "user-time-zone-unknown", {"candidate": candidate})


def _to_invalid_field_response(field: str, code: str, params: Mapping[str, object]) -> RegisterUserResponse:
    """Hilfsfunktion: erstelle aus einem Feldfehler die Response."""
    field_errors = [FieldError(field, code, params)]
    return to_invalid_response(field_errors)


def to_invalid_response(errors: Iterable[FieldError]) -> RegisterUserResponse:
    """Uebersetze gesammelte Feldfehler in die public Antwort."""
    return RegistrationInvalid(group_by_field(errors))
