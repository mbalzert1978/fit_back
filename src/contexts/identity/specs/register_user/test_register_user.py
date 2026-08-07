"""Verhaltens-Specs des Use Case RegisterUser.

Arrange laeuft ueber die Test-API, Act ueber das echte Request-DTO, Assert gegen
die echte Response-Union. Kein Spec importiert Handler, Mapper, Adapter, Fake
oder Domaene - was hier nicht ausdrueckbar ist, fehlt der public Oberflaeche
des Slice.

Diese Specs laufen ohne Datenbank, ohne HTTP und ohne Container.
"""

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
    """Test account creation returns correct user data."""
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
    heiligabend_2026_18_uhr_utc = 1798221600
    api = RegisterUserTestApi().at_unix_time(heiligabend_2026_18_uhr_utc)

    result = await api.run(_request())

    assert isinstance(result, RegistrationAccepted)
    assert result.registered_at_unix == heiligabend_2026_18_uhr_utc


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
async def test_lehnt_die_zweite_registrierung_derselben_email_ab() -> None:
    api = RegisterUserTestApi()

    first = await api.run(_request())
    second = await api.run(_request(display_name="Jemand anderes"))

    assert isinstance(first, RegistrationAccepted)
    assert isinstance(second, EmailAlreadyTaken)


@pytest.mark.asyncio
async def test_lehnt_ein_passwort_unter_zehn_zeichen_ab() -> None:
    api = RegisterUserTestApi()

    result = await api.run(_request(password="kurz"))

    assert isinstance(result, RegistrationInvalid)
    assert "password" in result.errors
    # Beleg: Der Code und Parameter sind Teil der Response-Union (nicht nur Texte)
    password_errors = result.errors["password"]
    assert len(password_errors) == 1
    code, params = password_errors[0]
    assert code == "password-too-short"
    assert params["minimum"] == 10
    assert params["actual_length"] == 4


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


@pytest.mark.asyncio
async def test_meldet_die_registrierung_nach_aussen() -> None:
    heiligabend_2026_18_uhr_utc = 1798221600
    api = RegisterUserTestApi().at_unix_time(heiligabend_2026_18_uhr_utc)

    result = await api.run(_request(locale="de"))

    assert isinstance(result, RegistrationAccepted)
    (announced,) = api.published_events
    assert announced.event_type == "UserRegistered"
    assert announced.occurred_at == heiligabend_2026_18_uhr_utc
    assert announced.payload == {"user_id": result.user_id, "locale": "de"}


@pytest.mark.asyncio
async def test_meldet_nichts_wenn_die_email_schon_vergeben_ist() -> None:
    api = RegisterUserTestApi().with_registered_user("markus@example.de")

    result = await api.run(_request(email="markus@example.de"))

    assert isinstance(result, EmailAlreadyTaken)
    assert api.published_events == ()


@pytest.mark.asyncio
async def test_meldet_nichts_bei_ungueltiger_eingabe() -> None:
    api = RegisterUserTestApi()

    result = await api.run(_request(password="kurz"))

    assert isinstance(result, RegistrationInvalid)
    assert api.published_events == ()


@pytest.mark.asyncio
async def test_email_error_codes_und_parameter_sind_in_der_response() -> None:
    """Beleg: Fehler-Codes fliessen durch die Naht in die Response-Union.

    Arrange (Test-API) → Act (Request-DTO) → Assert (Response-Union).
    Der HTTP-Rand wird diese Codes später mit Accept-Language uebersetzen,
    aber schon hier sind sie typisiert und parametrisiert.
    """
    api = RegisterUserTestApi()

    result = await api.run(_request(email="keine-at"))

    assert isinstance(result, RegistrationInvalid)
    assert "email" in result.errors
    email_errors = result.errors["email"]
    assert len(email_errors) >= 1
    # Jeden Email-Error-Code verifizieren
    codes_found = {code for code, _ in email_errors}
    assert codes_found >= {"email-needs-exactly-one-at-sign"}


@pytest.mark.asyncio
async def test_display_name_error_code_in_response() -> None:
    """Beleg: DisplayNameError-Codes sind typisiert in der Response."""
    api = RegisterUserTestApi()

    result = await api.run(_request(display_name="   "))

    assert isinstance(result, RegistrationInvalid)
    assert "displayName" in result.errors
    dn_errors = result.errors["displayName"]
    code, _ = dn_errors[0]
    assert code == "display-name-is-empty"


@pytest.mark.asyncio
async def test_locale_error_code_in_response() -> None:
    """Beleg: LocaleError-Codes sind typisiert in der Response."""
    api = RegisterUserTestApi()

    result = await api.run(_request(locale="fr"))

    assert isinstance(result, RegistrationInvalid)
    assert "locale" in result.errors
    locale_errors = result.errors["locale"]
    code, params = locale_errors[0]
    assert code == "locale-not-supported"
    assert params["candidate"] == "fr"


@pytest.mark.asyncio
async def test_email_already_taken_code_in_response() -> None:
    """Beleg: EmailAlreadyTaken traegt seinen Code (nicht nur die Email)."""
    api = RegisterUserTestApi().with_registered_user("markus@example.de")

    result = await api.run(_request(email="markus@example.de"))

    assert isinstance(result, EmailAlreadyTaken)
    assert result.code == "email-already-registered"
    assert result.email == "markus@example.de"
