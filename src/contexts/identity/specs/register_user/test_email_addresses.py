"""Welche E-Mail-Adressen die Registrierung annimmt - und welche nicht.

Die Tabelle unten ist die Spezifikation der Adresspruefung. Sie stammt aus dem
Review zu Ticket 0011 und deckt genau die Faelle ab, die ein Gesamt-Regex
verschweigt: Label-Laenge, Bindestrich-Position, Unterstriche in der Domain,
IP-Literale, IPv6-Gruppenzahl, Zeilenumbrueche, quoted Local-Parts.

Geprueft wird ueber die Test-API, nicht gegen das `Email`-Value-Object direkt.
Das ist der Unterschied zwischen einem Test auf das **Ergebnis** und einem auf
das **Wie**: hier steht, dass eine Adresse angenommen oder mit `errors.email`
abgelehnt wird - nicht, in welcher Klasse, welcher Methode und welcher Regel das
entschieden wurde. Wandert die Pruefung morgen woandershin, bleibt diese Datei
unveraendert.

**Nicht** enthalten sind internationalisierte Domains. Ob `उदाहरण` ein gueltiges
IDN-Label ist, entscheidet IDNA/UTS-46, und das ist die Zusage einer externen
Bibliothek - wir testen sie so wenig, wie wir testen, ob `open()` Dateien
oeffnen kann.
"""

import pytest

from src.contexts.identity.application.register_user import (
    RegisterUserRequest,
    RegisterUserTestApi,
    RegistrationAccepted,
    RegistrationInvalid,
)

_CASES: list[tuple[str, bool]] = [
    # --- gueltig: gewoehnliche Adressen ---
    ("email@here.com", True),
    ("weirder-email@here.and.there.com", True),
    ("!def!xyz%abc@example.com", True),
    ("example@valid-----hyphens.com", True),
    ("example@valid-with-hyphens.com", True),
    ("abc@bar", True),
    # --- gueltig: IP-Literale und blanke IPs ---
    ("email@[127.0.0.1]", True),
    ("email@[2001:dB8::1]", True),
    ("email@[2001:dB8:0:0:0:0:0:1]", True),
    ("email@[::fffF:127.0.0.1]", True),
    ("email@127.0.0.1", True),
    # --- Label-Laenge: 63 Zeichen sind erlaubt, 64 nicht (RFC 1034) ---
    ("a@atm." + "a" * 63, True),
    ("a@" + "a" * 63 + ".atm", True),
    ("a@" + "a" * 63 + ".bbbbbbbbbb.atm", True),
    ("a@atm." + "a" * 64, False),
    # --- Struktur ---
    ("", False),
    ("abc", False),
    ("abc@", False),
    ("something@@somewhere.com", False),
    ('"test@test"@example.com', False),
    # --- Leerraum ---
    # Leerzeichen und Tabulator werden abgeschnitten, bevor die Adresse geprueft
    # wird (`is_not_blank` als erste Regel der Kette) - ein Zeilenumbruch bleibt
    # stehen und faellt bei `has_no_whitespace` durch, egal ob er am Rand oder
    # **innerhalb** der Adresse steht.
    ("a @x.cz", False),
    ("a@b.com\n", False),
    ("a\n@b.com", False),
    ("a@[127.0.0.1]\n", False),
    (r'test@example.com\n\n<script src="x.js">', False),
    (r'"test@test"\n@example.com', False),
    (r'"\\\011"@here.com', False),
    (r'"\\\012"@here.com', False),
    # --- Domain-Labels ---
    ("abc@.com", False),
    ("trailingdot@shouldfail.com.", False),
    ("example@invalid-.com", False),
    ("example@-invalid.com", False),
    ("example@invalid.com-", False),
    ("example@inv-.alid-.com", False),
    ("example@inv-.-alid.com", False),
    ("John.Doe@exam_ple.com", False),
    # --- IP-Literale, die keine sind ---
    ("email@[127.0.0.256]", False),
    ("email@[2001:db8::12345]", False),
    ("email@[2001:db8:0:0:0:0:1]", False),
    ("email@[::ffff:127.0.0.256]", False),
]


def _request(email: str) -> RegisterUserRequest:
    """Ein ansonsten gueltiger Request - nur die Adresse variiert."""
    return RegisterUserRequest(
        email=email,
        password="ein-langes-passwort",
        display_name="Markus",
        locale="de",
        time_zone_id="Europe/Berlin",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("address", "expected_accepted"), _CASES)
async def test_nimmt_genau_die_spezifizierten_adressen_an(
    address: str,
    expected_accepted: bool,
) -> None:
    result = await RegisterUserTestApi().run(_request(address))

    assert isinstance(result, RegistrationAccepted) is expected_accepted
    if not expected_accepted:
        assert isinstance(result, RegistrationInvalid)
        assert "email" in result.errors


@pytest.mark.asyncio
async def test_zwei_schreibweisen_derselben_adresse_sind_dasselbe_konto() -> None:
    api = RegisterUserTestApi().with_registered_user("Markus@Example.DE")

    result = await api.run(_request("  markus@example.de  "))

    assert not isinstance(result, RegistrationAccepted)
