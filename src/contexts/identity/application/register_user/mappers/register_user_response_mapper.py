"""Response-Mapper: Ergebnis -> public Response-Union. Eine Richtung, kein Hinweg."""

from typing import assert_never

from src.contexts.identity.application.register_user.errors import (
    RegisterUserError,
    RequestInvalid,
)
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import EmailAlreadyRegistered, locale_tag
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import group_by_field

__all__ = ["to_response"]


def to_response(outcome: Result[Registration, RegisterUserError]) -> RegisterUserResponse:
    """Uebersetze den Ausgang der Pipeline in die public Antwort.

    Hier wird gematcht statt `map`/`bind` verkettet, und das ist Absicht: aus
    einem `Result` werden drei **verschiedene** Response-Typen. Die Kette kaeme da
    durchaus heraus - `map` plus `map_err` und eine Extraktion aus dem
    `Result[Response, Response]` am Ende. Sie traegt bis dorthin aber eine
    Unterscheidung weiter, die der naechste Schritt ohnehin einebnet, und verteilt
    die Response-Erzeugung auf zwei Funktionen plus einen Einsammelschritt, statt
    sie an **einer** Stelle zu halten. `assert_never` bliebe in beiden Formen
    erhalten - in der Kette waende es im `map_err` ueber die Fehler-Union; es
    spricht fuer keine der beiden.

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

    **Zwei Stufen statt einer**, und das ist keine Ziererei: erst der Ausgang,
    dann der Fehlerwert selbst. Stuenden die Fehlerfaelle wie zuvor verschachtelt
    im Muster (`case Err(error=RequestInvalid())`), traegt `ty` die Einengung
    nicht ins Typargument von `Err` hinein - der Restfall bliebe fuer den Pruefer
    `Err[RegisterUserError]` statt `Never`, und `assert_never` waere nur noch
    Laufzeitschutz. Auf dem Fehlerwert selbst gematcht, rechnet `ty` die
    Vollzaehligkeit aus; beide `assert_never` sind damit **statisch** belegt.
    """
    match outcome:
        case Ok(value=Registration(user=user, session=session)):
            return RegistrationAccepted(
                user_id=str(user.id),
                email=user.email.value,
                display_name=user.display_name.value,
                locale=locale_tag(user.locale),
                time_zone_id=user.time_zone.value,
                registered_at_unix=user.registered_at.unix_seconds,
                access_token=session.access_token,
                expires_in=session.expires_in,
                refresh_token=session.refresh_token,
                refresh_expires_in=session.refresh_expires_in,
            )
        case Err(error=error):
            match error:
                case RequestInvalid(errors=errors):
                    return RegistrationInvalid(group_by_field(errors))
                case EmailAlreadyRegistered(email=email):
                    return EmailAlreadyTaken(email.value)
                case _:
                    assert_never(error)
        case _:
            assert_never(outcome)
