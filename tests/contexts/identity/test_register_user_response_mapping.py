"""Der eine Fold des Slice RegisterUser: `Result[Registration, RegisterUserError]` -> Response.

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

from datetime import UTC, datetime

import pytest

from src.contexts.identity.application.register_user.adapters import (
    IdnEncoderAdapter,
    PasswordHasherAdapter,
)
from src.contexts.identity.application.register_user.adapters.test_api.fakes import (
    DeterministicPasswordHasher,
    PassthroughIdnLabels,
)
from src.contexts.identity.application.register_user.errors import request_invalid
from src.contexts.identity.application.register_user.mappers.register_user_response_mapper import (
    to_response,
)
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import (
    Email,
    EmailAlreadyRegistered,
    Session,
    User,
    UserFactory,
)
from src.contexts.shared_kernel import Err, FakeTimeProvider, Ok
from src.contexts.shared_kernel.validation import FieldError

REGISTRIERT_AM = 1798221600


def _email(raw: str) -> Email:
    """Baue die Adresse ueber denselben Weg wie die Produktion."""
    return Email.hydrate(raw, IdnEncoderAdapter(PassthroughIdnLabels()))


async def _user() -> User:
    """Baue die Wurzel ueber denselben Weg wie die Produktion - `User.create`.

    Seit die Wurzel ihre Value Objects selbst baut, gibt es keinen zweiten Weg zu
    einem `User` mehr. Der Test nimmt deshalb dieselben Fakes wie die Specs; die
    Uhr steht fest, damit `registered_at` pruefbar bleibt.
    """
    fabrik = UserFactory(
        idn=IdnEncoderAdapter(PassthroughIdnLabels()),
        hasher=PasswordHasherAdapter(DeterministicPasswordHasher()),
        clock=FakeTimeProvider(datetime.fromtimestamp(REGISTRIERT_AM, UTC)),
    )
    erzeugt = await fabrik.create(
        email="markus@example.de",
        password="geheim-genug-fuer-alle",
        display_name="Markus",
        locale="de",
        time_zone="Europe/Berlin",
    )
    match erzeugt:
        case Ok(value=user):
            return user
        case Err(error=rejected):
            msg = f"unreachable: gueltige Eingabe wurde abgelehnt - {rejected}"
            raise AssertionError(msg)


@pytest.mark.asyncio
async def test_ein_ok_wird_zur_angenommenen_registrierung() -> None:
    """Der Erfolgsfall traegt Stammdaten und Sitzung als Primitive nach aussen."""
    user = await _user()

    session = Session.hydrate(
        access_token="ein-access-token",
        expires_in=900,
        refresh_token="ein-refresh-token",
        refresh_expires_in=5_184_000,
    )

    antwort = to_response(Ok(Registration(user, session)))

    assert antwort == RegistrationAccepted(
        user_id=str(user.id),
        email="markus@example.de",
        display_name="Markus",
        locale="de",
        time_zone_id="Europe/Berlin",
        registered_at_unix=REGISTRIERT_AM,
        access_token="ein-access-token",
        expires_in=900,
        refresh_token="ein-refresh-token",
        refresh_expires_in=5_184_000,
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
