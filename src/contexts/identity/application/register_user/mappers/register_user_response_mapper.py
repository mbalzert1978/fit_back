"""Response-Mapper: Ergebnis -> public Response-Union. Eine Richtung, kein Hinweg."""

from collections.abc import Iterable

from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import (
    DomainError,
    EmailAlreadyRegistered,
    User,
    locale_tag,
)
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import FieldError, group_by_field

__all__ = ["to_invalid_response", "to_response"]


class PipelineBroken(RuntimeError):
    """Der Handler meldete einen Fehler, den die Pipeline ausgeschlossen hatte.

    Kein Fachfall, sondern ein Programmierfehler: `RegisterUserPipeline.run`
    validiert erst vollstaendig und baut das Command danach mit `hydrate` - alle
    Value-Object-Fehler sind zu diesem Zeitpunkt bereits ausgeschlossen. Trifft
    hier trotzdem einer ein, ist die Reihenfolge in der Pipeline zerbrochen, und
    eine 400er-Antwort wuerde das als Eingabefehler des Aufrufers ausgeben.
    """

    def __init__(self, error: DomainError) -> None:
        """Nenne den Fall, der nicht haette ankommen koennen."""
        super().__init__(
            f"{type(error).__name__} hat den Response-Mapper erreicht, obwohl die "
            f"Validierung der Pipeline ihn ausschliesst. Die Pipeline ist defekt, "
            f"nicht die Eingabe."
        )
        self.error = error


def to_response(outcome: Result[User, DomainError]) -> RegisterUserResponse:
    """Uebersetze den Domaenen-Ausgang in die public Antwort.

    Hier wird gematcht statt `map`/`bind` verkettet, und das ist Absicht: aus
    `Result[User, DomainError]` werden zwei **verschiedene** Response-Typen. Das
    ist ein Fold aus dem `Result` heraus, keine Transformation darin - `map`
    kaeme nie aus dem Ok-Zweig heraus.

    Erreichbar sind genau zwei Ausgaenge. `RegisterUserPipeline.run` laesst nur
    einen vollstaendig validierten Request bis zum Handler durch und baut das
    Command mit `hydrate` statt `parse`; damit kann die Fehlerhaelfte des
    `Result` nur noch `EmailAlreadyRegistered` vom Port tragen. Jeder andere Fall
    ist ein Bug in der Pipeline und wird als solcher laut - er wird **nicht** in
    einen Feldfehler zurueckuebersetzt.

    Das ist auch der Grund, warum die Code+Parameter-Tabelle der Feldfehler hier
    nicht noch einmal steht: sie gehoert zur Validierung und lebt einmalig in
    `validators/register_user_rules.py`. Eine zweite Abschrift an dieser Stelle
    waere eine Wahrheit zu viel - genau die Drift, gegen die dieser Slice den
    Startup-Check hat.

    Der Abschlusszweig wirft `PipelineBroken` und **nicht** `assert_never`, und
    das ist der Unterschied, auf den es hier ankommt: `PasswordTooShort` & Co.
    sind gueltige `DomainError`-Werte, ihr Auftreten ist also nicht typmaessig
    unmoeglich, sondern nur durch die Reihenfolge in der Pipeline ausgeschlossen.
    `assert_never` behauptete an dieser Stelle etwas Falsches - und wuerde bei
    einem Bruch nur "unerwarteter Wert" melden, wo `PipelineBroken` sagt, welche
    Annahme gebrochen ist (.rules/python/python-error-handling.md, "Jeder `match`
    ist vollstaendig").

    Welche Faelle abgebildet und welche ausgeschlossen sind, haelt
    `tests/contexts/identity/test_register_user_response_mapping.py` fest;
    waechst `DomainError`, wird der Test rot und verlangt die Entscheidung.
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
        case Err(error=error):
            raise PipelineBroken(error)


def to_invalid_response(errors: Iterable[FieldError]) -> RegisterUserResponse:
    """Uebersetze gesammelte Feldfehler in die public Antwort."""
    return RegistrationInvalid(group_by_field(errors))
