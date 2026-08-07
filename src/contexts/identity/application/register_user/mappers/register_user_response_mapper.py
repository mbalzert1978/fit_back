"""Response-Mapper: Ergebnis -> public Response-Union. Eine Richtung, kein Hinweg."""

from collections.abc import Iterable
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


def to_response(outcome: Result[User, DomainError]) -> RegisterUserResponse:
    """Uebersetze den Domaenen-Ausgang in die public Antwort.

    Hier wird gematcht statt `map`/`bind` verkettet, und das ist Absicht: aus
    `Result[User, DomainError]` werden zwei **verschiedene** Response-Typen. Das
    ist ein Fold aus dem `Result` heraus, keine Transformation darin - `map`
    kaeme nie aus dem Ok-Zweig heraus.

    **Jeder Fall von `DomainError` ist unten namentlich aufgezaehlt**, und erst
    danach steht `case _: assert_never(outcome)`. Das ist der ganze Sinn des
    Abschlusszweigs: er soll melden, dass jemand die Union *erweitert* hat.
    Stuenden davor nur die behandelten Faelle, finge er auch alles ab, was es
    laengst gibt und nur niemand angefasst hat - dann liesse sich "neu
    dazugekommen" nicht mehr von "seit jeher unbehandelt" unterscheiden, und die
    Meldung waere wertlos. `assert_never` gehoert ans Ende einer erschoepften
    Aufzaehlung, sonst behauptet es etwas Falsches
    (.rules/python/python-error-handling.md, "Jeder `match` ist vollstaendig").

    Fachlich beantwortet wird genau ein Fehlerfall. `RegisterUserPipeline.run`
    laesst nur einen vollstaendig validierten Request bis zum Handler durch und
    baut das Command mit `hydrate` statt `parse`; damit kann die Fehlerhaelfte
    des `Result` nur `EmailAlreadyRegistered` vom Port tragen. Die uebrigen 21
    Faelle sind dadurch ausgeschlossen - sie stehen im Sammelarm und scheitern
    laut, statt in einen Feldfehler zurueckuebersetzt zu werden: ihr Auftreten
    hiesse, dass die Reihenfolge in der Pipeline kaputt ist, und eine
    400er-Antwort gaebe das faelschlich als Eingabefehler des Aufrufers aus.

    Der Sammelarm zaehlt sie einzeln auf, statt sie mit einem Muster zu
    erschlagen - genau davon lebt die Unterscheidung oben. Er bildet sie aber
    **nicht** auf Code und Parameter ab: diese Tabelle gehoert zur Validierung
    und lebt einmalig in `validators/register_user_rules.py`. Eine zweite
    Abschrift hier waere eine Wahrheit zu viel.

    Welche Faelle abgebildet und welche ausgeschlossen sind, haelt
    `tests/contexts/identity/test_register_user_response_mapping.py` fest.
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
        case Err(
            error=(
                EmailHasWhitespace()
                | EmailNeedsExactlyOneAtSign()
                | EmailLocalPartMissing()
                | EmailDomainMissing()
                | EmailLocalPartTooLong()
                | EmailLocalPartHasInvalidCharacters()
                | EmailLocalPartHasMisplacedDot()
                | EmailDomainTooLong()
                | EmailDomainHasEmptyLabel()
                | EmailDomainLabelTooLong()
                | EmailDomainLabelHasEdgeHyphen()
                | EmailDomainLabelHasInvalidCharacters()
                | EmailAddressLiteralInvalid()
                | UnencodableDomainLabel()
                | PasswordTooShort()
                | DisplayNameIsEmpty()
                | DisplayNameTooLong()
                | LocaleNotSupported()
                | PasswordHashIsEmpty()
                | UserIdMalformed()
                | UserTimeZoneUnknown()
            ) as ausgeschlossen
        ):
            msg = (
                f"{type(ausgeschlossen).__name__} hat den Response-Mapper erreicht, "
                f"obwohl die Validierung der Pipeline ihn ausschliesst. Die Pipeline "
                f"ist defekt, nicht die Eingabe."
            )
            raise AssertionError(msg)
        case _:
            assert_never(outcome)


def to_invalid_response(errors: Iterable[FieldError]) -> RegisterUserResponse:
    """Uebersetze gesammelte Feldfehler in die public Antwort."""
    return RegistrationInvalid(group_by_field(errors))
