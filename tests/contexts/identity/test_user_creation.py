"""`User.create` - die Wurzel baut ihre Value Objects selbst und sammelt ihre Befunde.

Hier steht die einzige Pruefung der Registrierung. Deshalb misst dieser Test nicht
nur, **dass** abgelehnt wird, sondern auch **wieviel** auf einmal und **in welcher
Reihenfolge** - das uebernimmt der Rand unveraendert in den 422 des Vertrags.
"""

from datetime import UTC, datetime

import pytest

from src.contexts.identity.application.register_user.adapters import (
    IdnEncoderAdapter,
    PasswordHasherAdapter,
)
from src.contexts.identity.application.register_user.fakes import (
    DeterministicPasswordHasher,
    PassthroughIdnLabels,
)
from src.contexts.identity.domain import (
    Active,
    DisplayNameRejected,
    DisplayNameTooShort,
    EmailRejected,
    EmailIsEmpty,
    German,
    LocaleNotSupported,
    LocaleRejected,
    PasswordRejected,
    PasswordTooShort,
    TimeZoneRejected,
    User,
    UserRejected,
    UserTimeZoneUnknown,
)
from src.contexts.shared_kernel import Err, FakeTimeProvider, Ok

REGISTRIERT_AM = 1798221600

GUELTIG = {
    "email": "Markus@Example.de",
    "password": "geheim-genug-fuer-alle",
    "display_name": "Markus",
    "locale": "de",
    "time_zone": "GMT+01:00",
}


async def _create(**abweichend: str) -> object:
    """Rufe `User.create` mit gueltiger Eingabe, ausser wo der Test abweicht."""
    return await User.create(
        **(GUELTIG | abweichend),
        idn=IdnEncoderAdapter(PassthroughIdnLabels()),
        hasher=PasswordHasherAdapter(DeterministicPasswordHasher()),
        clock=FakeTimeProvider(datetime.fromtimestamp(REGISTRIERT_AM, UTC)),
    )


@pytest.mark.asyncio
async def test_gueltige_rohwerte_werden_zur_aktiven_wurzel() -> None:
    """Beleg: `create` normalisiert, hasht, stempelt - und setzt `Active`."""
    erzeugt = await _create()

    match erzeugt:
        case Ok(value=user):
            assert user.email.value == "markus@example.de"
            assert user.display_name.value == "Markus"
            assert user.locale == German()
            assert user.time_zone.value == "+01:00"
            assert user.status == Active()
            assert user.registered_at.unix_seconds == REGISTRIERT_AM
            assert user.password_hash.value.startswith("fake-argon2id$")
        case _:
            pytest.fail(f"gueltige Eingabe wurde abgelehnt: {erzeugt}")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("abweichend", "erwartet"),
    [
        pytest.param({"email": "   "}, EmailRejected(EmailIsEmpty()), id="email"),
        pytest.param(
            {"password": "zu-kurz"},
            PasswordRejected(PasswordTooShort(7, 10)),
            id="password",
        ),
        pytest.param(
            {"display_name": "a"},
            DisplayNameRejected(DisplayNameTooShort(1, 2)),
            id="display-name",
        ),
        pytest.param(
            {"locale": "fr"},
            LocaleRejected(LocaleNotSupported("fr")),
            id="locale",
        ),
        pytest.param(
            {"time_zone": "Europe/Nirgendwo"},
            TimeZoneRejected(UserTimeZoneUnknown("Europe/Nirgendwo")),
            id="time-zone",
        ),
    ],
)
async def test_ein_ungueltiges_feld_wird_mit_seinem_namen_abgelehnt(
    abweichend: dict[str, str], erwartet: object
) -> None:
    """Beleg: der Fehler sagt, **welches** Feld gescheitert ist - nicht nur, dass eines.

    Der Grund fuer die fuenf Huellen in `user_creation_errors.py`: eine flache
    Union der Parser-Fehler liesse die Zuordnung zum Feld nur erraten.
    """
    assert await _create(**abweichend) == Err(UserRejected((erwartet,)))


@pytest.mark.asyncio
async def test_alle_ungueltigen_felder_werden_auf_einmal_gemeldet() -> None:
    """Beleg: die Wurzel sammelt ihre Befunde, statt beim ersten abzubrechen.

    Solange `create` das leistet, braucht der Slice kein zweites Regelwerk davor.
    """
    abgelehnt = await _create(email="   ", password="zu-kurz", locale="fr")

    assert abgelehnt == Err(
        UserRejected(
            (
                EmailRejected(EmailIsEmpty()),
                PasswordRejected(PasswordTooShort(7, 10)),
                LocaleRejected(LocaleNotSupported("fr")),
            )
        )
    )


@pytest.mark.asyncio
async def test_die_reihenfolge_der_befunde_ist_die_feldreihenfolge() -> None:
    """Beleg: gemeldet wird in der Reihenfolge der Felder, nicht nach Zufall."""
    abgelehnt = await _create(display_name="a", time_zone="Europe/Nirgendwo", password="kurz")

    match abgelehnt:
        case Err(error=UserRejected(rejections=befunde)):
            assert [type(befund) for befund in befunde] == [
                PasswordRejected,
                DisplayNameRejected,
                TimeZoneRejected,
            ]
        case _:
            pytest.fail(f"erwartet war eine Ablehnung, gekommen ist: {abgelehnt}")
