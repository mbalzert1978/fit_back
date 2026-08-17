"""Der eine Fold des Slice RegisterUser: `Result[User, RegisterUserError]` -> Response.

Bis Stufe 3 stand hier ein Test ueber die **Struktur** einer Zuordnung, weil
`to_response` zweiundzwanzig Arme hatte, von denen einer erreichbar war: die
Validierung fing vorher alles ab, `to_command` baut mit `hydrate` (infallibel),
und die uebrigen Arme liessen sich nur ueber von Hand gebaute Eingaben ansteuern,
die der laufende Code nie erzeugt - ein gruener Test ueber Fiktion.

Mit der Behavior-Kette (Stufe 4) tragen beide Wege denselben Fehlertyp, und
`to_response` hat drei Arme plus `assert_never`. **Alle drei sind erreichbar**,
also werden sie hier auch alle drei gefahren - direkt gegen den Mapper, weil
genau er das Pruefobjekt ist. Dass dieselben drei Ausgaenge auch am Ende des
echten Use Case herauskommen, belegen die Specs unter
`src/contexts/identity/specs/register_user/`.

Regel: `.rules/python/python-error-handling.md`, "Jeder `match` ist vollstaendig".
"""

from src.contexts.identity.application.register_user.adapters import IdnEncoderAdapter
from src.contexts.identity.application.register_user.errors import request_invalid
from src.contexts.identity.application.register_user.fakes import PassthroughIdnLabels
from src.contexts.identity.application.register_user.mappers.register_user_response_mapper import (
    to_response,
)
from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import (
    DisplayName,
    Email,
    EmailAlreadyRegistered,
    PasswordHash,
    UserId,
    UserTimeZone,
    hydrate_locale,
    register,
)
from src.contexts.shared_kernel import Err, Ok, Timestamp
from src.contexts.shared_kernel.validation import FieldError

REGISTRIERT_AM = 1798221600


def _email(raw: str) -> Email:
    """Baue die Adresse ueber denselben Weg wie die Produktion."""
    return Email.hydrate(raw, IdnEncoderAdapter(PassthroughIdnLabels()))


def test_ein_ok_wird_zur_angenommenen_registrierung() -> None:
    """Der Erfolgsfall traegt die Stammdaten als Primitive nach aussen."""
    user = register(
        user_id=UserId.generate(),
        email=_email("markus@example.de"),
        password_hash=PasswordHash.hydrate("argon2id$…"),
        display_name=DisplayName.hydrate("Markus"),
        time_zone=UserTimeZone.hydrate("Europe/Berlin"),
        locale=hydrate_locale("de"),
        registered_at=Timestamp(REGISTRIERT_AM),
    )

    antwort = to_response(Ok(user))

    assert antwort == RegistrationAccepted(
        user_id=str(user.id),
        email="markus@example.de",
        display_name="Markus",
        locale="de",
        time_zone_id="Europe/Berlin",
        registered_at_unix=REGISTRIERT_AM,
    )


def test_ungueltige_eingabe_wird_zur_feldfehler_antwort() -> None:
    """Der Weg, den frueher ein zweiter Fold nahm - jetzt ein Arm wie die anderen."""
    antwort = to_response(
        Err(
            request_invalid(
                [
                    FieldError("password", "password-too-short", {"minimum": 10}),
                    FieldError("locale", "locale-not-supported", {"candidate": "fr"}),
                ]
            )
        )
    )

    assert antwort == RegistrationInvalid(
        {
            "password": (("password-too-short", {"minimum": 10}),),
            "locale": (("locale-not-supported", {"candidate": "fr"}),),
        }
    )


def test_mehrere_befunde_zum_selben_feld_bleiben_beisammen() -> None:
    """`group_by_field` fasst je Feld zusammen, verwirft aber keinen Befund."""
    antwort = to_response(
        Err(
            request_invalid(
                [
                    FieldError("email", "email-has-whitespace", {}),
                    FieldError("email", "email-domain-missing", {}),
                ]
            )
        )
    )

    assert antwort == RegistrationInvalid(
        {"email": (("email-has-whitespace", {}), ("email-domain-missing", {}))}
    )


def test_die_email_kollision_wird_nicht_zum_feldfehler() -> None:
    """Eigener Ausgang mit eigenem Statuscode - kein Eintrag in `errors`."""
    antwort = to_response(Err(EmailAlreadyRegistered(_email("besetzt@example.com"))))

    assert antwort == EmailAlreadyTaken("besetzt@example.com")
