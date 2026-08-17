"""Response-Mapper: Ergebnis -> public Response-Union. Eine Richtung, kein Hinweg."""

from typing import assert_never

from src.contexts.identity.application.register_user.errors import (
    RegisterUserError,
    RequestInvalid,
)
from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import EmailAlreadyRegistered, User, locale_tag
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import group_by_field

__all__ = ["to_response"]


def to_response(outcome: Result[User, RegisterUserError]) -> RegisterUserResponse:
    """Uebersetze den Ausgang der Pipeline in die public Antwort.

    Hier wird gematcht statt `map`/`bind` verkettet, und das ist Absicht: aus
    einem `Result` werden drei **verschiedene** Response-Typen. Das ist ein Fold
    aus dem `Result` heraus, keine Transformation darin - `map` kaeme nie aus dem
    Ok-Zweig heraus.

    **Der eine Fold des Slice.** Bis Stufe 3 gab es zwei - einen fuer die
    Feldfehler aus der Validierung, einen fuer den Domaenenfehler aus dem
    Handler -, verbunden durch ein `if` in der Pipeline. Seit die Validierung
    das erste Behavior der Kette ist, tragen beide Wege denselben Fehlertyp
    (`RegisterUserError`) und muenden hier.

    **Drei Arme, alle erreichbar**, und `assert_never` dahinter. Das ist der
    Unterschied zum frueheren Stand: dort standen zweiundzwanzig Arme, von denen
    einer je vorkam, weil die Validierung alles andere vorher abfing und
    `to_command` infallibel baut. Ein Abschlusszweig hinter lauter
    unerreichbaren Armen kann "neu dazugekommen" nicht mehr von "gibt es laengst,
    hat nur niemand behandelt" unterscheiden; hinter drei erreichbaren kann er
    es.

    Damit entfaellt auch die zweite Abschrift der Code-und-Parameter-Tabelle aus
    `validators/register_user_rules.py`: die Feldfehler kommen als Werte an,
    nicht als Faelle, die hier noch einmal benannt werden muessten.
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
        case Err(error=RequestInvalid(errors=errors)):
            return RegistrationInvalid(group_by_field(errors))
        case Err(error=EmailAlreadyRegistered(email=email)):
            return EmailAlreadyTaken(email.value)
        case _:
            assert_never(outcome)
