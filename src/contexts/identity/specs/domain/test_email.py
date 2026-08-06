"""Domain-Unit-Test des Value Object Email.

Die Tabelle unten **ist** die Spezifikation der Adresspruefung - sie stammt aus
dem Review zu Ticket 0011 und deckt genau die Faelle ab, die ein
Gesamt-Regex verschweigt: Label-Laenge, Bindestrich-Position, Unterstriche in der
Domain, IP-Literale, IPv6-Gruppenzahl, Zeilenumbrueche, quoted Local-Parts.

Wer eine Regel in `domain/value_objects/email.py` aendert, aendert eine Zeile
hier mit - oder er hat die Regel nicht verstanden.
"""

import pytest

from src.contexts.identity.application.register_user.adapters import IdnEncoderAdapter
from src.contexts.identity.domain import Email
from src.contexts.identity.infrastructure.idn import IdnaLabels
from src.shared_kernel import Ok

_IDN = IdnEncoderAdapter(IdnaLabels())
"""Die **echte** IDN-Bibliothek, nicht der Fake des Slice.

Ein Domain-Unit-Test darf tiefer greifen als ein Slice-Spec - das ist sein Zweck
(docs/milestones/02-test-pyramide.md, unterste Ebene). Und hier muss er es: die
Tabelle unten ist die Spezifikation der Adresspruefung, und gegen einen
nachgebauten Punycode-Fake wuerde sie nur sich selbst bestaetigen.
"""

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
    # --- gueltig: internationalisierte Domainnamen ---
    ("test@domain.with.idn.tld.उदाहरण.परीक्षा", True),
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


@pytest.mark.parametrize(("candidate", "expected_valid"), _CASES)
def test_akzeptiert_genau_die_spezifizierten_adressen(candidate: str, expected_valid: bool) -> None:
    assert isinstance(Email.parse(candidate, _IDN), Ok) is expected_valid


def test_normalisiert_gross_kleinschreibung_und_umgebenden_leerraum() -> None:
    assert Email.parse("  Markus@Example.DE  ", _IDN) == Ok(Email("markus@example.de"))


def test_zwei_schreibweisen_derselben_adresse_sind_gleich() -> None:
    assert Email.hydrate("Markus@Example.DE", _IDN) == Email.hydrate("markus@example.de", _IDN)
