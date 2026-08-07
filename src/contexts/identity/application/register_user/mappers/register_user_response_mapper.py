"""Response-Mapper: Ergebnis -> public Response-Union. Eine Richtung, kein Hinweg."""

from collections.abc import Iterable, Mapping
from typing import assert_never

from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import (
    DisplayNameIsEmpty,
    DisplayNameTooLong,
    DomainError,
    EmailAddressLiteralInvalid,
    EmailAlreadyRegistered,
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
    LocaleNotSupported,
    PasswordHashIsEmpty,
    PasswordTooShort,
    UnencodableDomainLabel,
    User,
    UserIdMalformed,
    UserTimeZoneUnknown,
    locale_tag,
)
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import FieldError, group_by_field

__all__ = ["to_invalid_response", "to_response"]

_EMAIL = "email"

_HASHER_BROKEN = (
    "PasswordHashIsEmpty hat den Response-Mapper erreicht. Der PasswordHasher-Port ist "
    "infallibel deklariert und der Adapter nutzt PasswordHash.hydrate - dieser Fall kann "
    "nur aus einem Bug im Hasher stammen und ist kein Eingabefehler des Aufrufers."
)

_ID_GENERATOR_BROKEN = (
    "UserIdMalformed hat den Response-Mapper erreicht. Die Identitaet stammt aus "
    "UserId.generate(), nicht aus der Anfrage - dieser Fall kann nur aus einem Bug in der "
    "Erzeugung stammen und ist kein Eingabefehler des Aufrufers."
)


def to_response(outcome: Result[User, DomainError]) -> RegisterUserResponse:
    """Uebersetze den Domaenen-Ausgang in die public Antwort.

    Hier wird gematcht statt `map`/`bind` verkettet, und das ist Absicht: aus
    `Result[User, DomainError]` werden zwei **verschiedene** Response-Typen. Das
    ist ein Fold aus dem `Result` heraus, keine Transformation darin - `map`
    kaeme nie aus dem Ok-Zweig heraus.

    **Jeder Fall von `DomainError` hat hier seinen eigenen Arm.** Kein
    Sammelmuster, das mehrere Faelle zusammenfasst: aus der Domaene fuehrt kein
    offener Punkt auf den oeffentlichen Pfad, und ein zusammengefasster Arm
    koennte nicht mehr sagen, *welcher* Fall vorlag. Dass die Code- und
    Parameter-Tabelle damit ein zweites Mal neben
    `validators/register_user_rules.py` steht, ist bewusst in Kauf genommen -
    das ist der Preis der Union, und er ist billiger als eine gemeinsame
    Zwischenschicht, die ihre Signatur ueber alle Fehlertypen spannen muesste
    (.rules/python/python-rule-pattern.md, Review-Checkliste).

    Erst **nach** der vollstaendigen Aufzaehlung steht `case _:
    assert_never(outcome)`. Nur so meldet der Abschlusszweig, was er melden soll:
    dass jemand `DomainError` erweitert hat. Stuenden davor nur die erwarteten
    Faelle, finge er auch alles ab, was es laengst gibt und nur niemand
    angefasst hat.

    Zwei Faelle liefern keine Antwort, sondern scheitern: `PasswordHashIsEmpty`
    und `UserIdMalformed` tragen als einzige keinen Fehlercode, weil sie den Rand
    nie erreichen sollen (`main.py`, `ERROR_UNIONS`). Sie stammen aus dem Hasher
    und aus `UserId.generate()`, nicht aus der Anfrage - es gibt keine Antwort,
    die dem Aufrufer etwas Wahres ueber sein eigenes Zutun sagen koennte.
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
            return _invalid(_EMAIL, EmailHasWhitespace.code, {})
        case Err(error=EmailNeedsExactlyOneAtSign(at_sign_count=count)):
            return _invalid(_EMAIL, EmailNeedsExactlyOneAtSign.code, {"at_sign_count": count})
        case Err(error=EmailLocalPartMissing()):
            return _invalid(_EMAIL, EmailLocalPartMissing.code, {})
        case Err(error=EmailDomainMissing()):
            return _invalid(_EMAIL, EmailDomainMissing.code, {})
        case Err(error=EmailLocalPartTooLong(maximum=maximum)):
            return _invalid(_EMAIL, EmailLocalPartTooLong.code, {"maximum": maximum})
        case Err(error=EmailLocalPartHasInvalidCharacters(invalid_characters=invalid)):
            return _invalid(
                _EMAIL,
                EmailLocalPartHasInvalidCharacters.code,
                {"invalid_characters": "".join(invalid)},
            )
        case Err(error=EmailLocalPartHasMisplacedDot()):
            return _invalid(_EMAIL, EmailLocalPartHasMisplacedDot.code, {})
        case Err(error=EmailDomainTooLong(maximum=maximum)):
            return _invalid(_EMAIL, EmailDomainTooLong.code, {"maximum": maximum})
        case Err(error=EmailDomainHasEmptyLabel()):
            return _invalid(_EMAIL, EmailDomainHasEmptyLabel.code, {})
        case Err(error=EmailDomainLabelTooLong(maximum=maximum)):
            return _invalid(_EMAIL, EmailDomainLabelTooLong.code, {"maximum": maximum})
        case Err(error=EmailDomainLabelHasEdgeHyphen()):
            return _invalid(_EMAIL, EmailDomainLabelHasEdgeHyphen.code, {})
        case Err(error=EmailDomainLabelHasInvalidCharacters()):
            return _invalid(_EMAIL, EmailDomainLabelHasInvalidCharacters.code, {})
        case Err(error=EmailAddressLiteralInvalid()):
            return _invalid(_EMAIL, EmailAddressLiteralInvalid.code, {})
        case Err(error=UnencodableDomainLabel(reason=reason)):
            return _invalid(_EMAIL, UnencodableDomainLabel.code, {"reason": reason})
        case Err(error=PasswordTooShort(actual_length=actual, minimum=minimum)):
            return _invalid(
                "password",
                PasswordTooShort.code,
                {"actual_length": actual, "minimum": minimum},
            )
        case Err(error=DisplayNameIsEmpty()):
            return _invalid("displayName", DisplayNameIsEmpty.code, {})
        case Err(error=DisplayNameTooLong(actual_length=actual, maximum=maximum)):
            return _invalid(
                "displayName",
                DisplayNameTooLong.code,
                {"actual_length": actual, "maximum": maximum},
            )
        case Err(error=LocaleNotSupported(candidate=candidate)):
            return _invalid("locale", LocaleNotSupported.code, {"candidate": candidate})
        case Err(error=UserTimeZoneUnknown(candidate=candidate)):
            return _invalid("timeZoneId", UserTimeZoneUnknown.code, {"candidate": candidate})
        case Err(error=PasswordHashIsEmpty()):
            raise AssertionError(_HASHER_BROKEN)
        case Err(error=UserIdMalformed()):
            raise AssertionError(_ID_GENERATOR_BROKEN)
        case _:
            assert_never(outcome)


def _invalid(field: str, code: str, parameters: Mapping[str, object]) -> RegisterUserResponse:
    """Baue die Antwort fuer genau einen Feldfehler."""
    return to_invalid_response([FieldError(field, code, parameters)])


def to_invalid_response(errors: Iterable[FieldError]) -> RegisterUserResponse:
    """Uebersetze gesammelte Feldfehler in die public Antwort."""
    return RegistrationInvalid(group_by_field(errors))
