"""Verhaltens-Specs des Use Case RegisterUser.

Arrange laeuft ueber die Test-API, Act ueber das echte Request-DTO, Assert gegen
die echte Response-Union. Kein Spec importiert Handler, Mapper, Adapter, Fake
oder Domaene - was hier nicht ausdrueckbar ist, fehlt der public Oberflaeche
des Slice.

Diese Specs laufen ohne Datenbank, ohne HTTP und ohne Container.
"""

from datetime import UTC, datetime

import pytest

from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegisterUserRequest,
    RegisterUserTestApi,
    RegistrationAccepted,
    RegistrationInvalid,
)


def _request(**overrides: str) -> RegisterUserRequest:
    """Baue einen gueltigen Registrierungs-Request, feldweise ueberschreibbar."""
    return RegisterUserRequest(
        **{
            "email": "markus@example.de",
            "password": "ein-langes-passwort",
            "display_name": "Markus",
            "locale": "de",
            "time_zone_id": "Europe/Berlin",
            **overrides,
        }
    )


@pytest.mark.asyncio
async def test_legt_ein_konto_an_und_gibt_die_stammdaten_zurueck() -> None:
    api = RegisterUserTestApi()

    result = await api.run(_request())

    assert isinstance(result, RegistrationAccepted)
    assert result.email == "markus@example.de"
    assert result.display_name == "Markus"
    assert result.locale == "de"
    assert result.time_zone_id == "Europe/Berlin"
    assert result.user_id


@pytest.mark.asyncio
async def test_registriert_zum_zeitpunkt_der_zeitquelle() -> None:
    moment = datetime(2026, 12, 24, 18, 0, tzinfo=UTC)
    api = RegisterUserTestApi().at_time(moment)

    result = await api.run(_request())

    assert isinstance(result, RegistrationAccepted)
    assert result.registered_at == moment


@pytest.mark.asyncio
async def test_normalisiert_die_email_vor_dem_speichern() -> None:
    api = RegisterUserTestApi()

    result = await api.run(_request(email="  Markus@Example.DE  "))

    assert isinstance(result, RegistrationAccepted)
    assert result.email == "markus@example.de"


@pytest.mark.asyncio
async def test_lehnt_eine_bereits_vergebene_email_ab() -> None:
    api = RegisterUserTestApi().with_registered_user("markus@example.de")

    result = await api.run(_request())

    assert isinstance(result, EmailAlreadyTaken)
    assert result.email == "markus@example.de"


@pytest.mark.asyncio
async def test_erkennt_die_vergebene_email_unabhaengig_von_gross_kleinschreibung() -> None:
    api = RegisterUserTestApi().with_registered_user("Markus@Example.DE")

    result = await api.run(_request(email="markus@example.de"))

    assert isinstance(result, EmailAlreadyTaken)


@pytest.mark.asyncio
async def test_lehnt_ab_wenn_die_email_zwischen_pruefung_und_schreiben_belegt_wird() -> None:
    api = RegisterUserTestApi().with_email_taken_between_check_and_write("markus@example.de")

    result = await api.run(_request())

    assert isinstance(result, EmailAlreadyTaken)
    assert result.email == "markus@example.de"


@pytest.mark.asyncio
async def test_lehnt_ein_passwort_unter_zehn_zeichen_ab() -> None:
    api = RegisterUserTestApi()

    result = await api.run(_request(password="kurz"))

    assert isinstance(result, RegistrationInvalid)
    assert "password" in result.errors


@pytest.mark.asyncio
async def test_meldet_alle_ungueltigen_felder_auf_einmal() -> None:
    api = RegisterUserTestApi()

    result = await api.run(
        _request(
            email="kein-at-zeichen",
            password="kurz",
            display_name="   ",
            locale="fr",
            time_zone_id="Mars/Olympus_Mons",
        )
    )

    assert isinstance(result, RegistrationInvalid)
    assert set(result.errors) == {"email", "password", "displayName", "locale", "timeZoneId"}


@pytest.mark.asyncio
async def test_legt_bei_ungueltiger_eingabe_kein_konto_an() -> None:
    api = RegisterUserTestApi()

    rejected = await api.run(_request(password="kurz"))
    accepted = await api.run(_request())

    assert isinstance(rejected, RegistrationInvalid)
    assert isinstance(accepted, RegistrationAccepted)
