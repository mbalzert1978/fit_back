"""Die Sperre gegen den rohen Konstruktor - fuer jedes Value Object des Contexts.

Bis hierher war "wird ausschliesslich ueber `parse` oder `hydrate` erzeugt" eine
Zusage in einer Docstring. `Email("quatsch")` ging trotzdem durch, und der Rest
des Systems rechnete danach mit einem Wert, den keine Regel je gesehen hatte.

Der Test steht je Value Object einmal und nicht als Schleife ueber eine Liste:
die Konstruktoren haben verschiedene Signaturen, und eine Schleife darueber
verstecke genau die Stelle, die hier zu belegen ist.
"""

from uuid import uuid7

import pytest

from src.contexts.identity.application.register_user.adapters import IdnEncoderAdapter
from src.contexts.identity.application.register_user.fakes import PassthroughIdnLabels
from src.contexts.identity.domain import (
    DisplayName,
    Email,
    Password,
    PasswordHash,
    UserId,
    UserTimeZone,
)
from src.contexts.shared_kernel import ConstructionKey


def test_der_rohe_konstruktor_verlangt_einen_schluessel() -> None:
    """Beleg: ohne Schluessel kommt der Aufruf gar nicht erst bis zum Rumpf."""
    with pytest.raises(TypeError):
        DisplayName("Markus")  # ty: ignore[missing-argument]


@pytest.mark.parametrize(
    ("bauen", "rohwert"),
    [
        pytest.param(DisplayName, "Markus", id="display-name"),
        pytest.param(Password, "geheim-genug-fuer-alle", id="password"),
        pytest.param(PasswordHash, "$argon2id$v=19$...", id="password-hash"),
        pytest.param(UserTimeZone, "Europe/Berlin", id="user-time-zone"),
        pytest.param(Email, "markus@example.de", id="email"),
    ],
)
def test_ein_fremder_schluessel_wird_abgewiesen(bauen: type, rohwert: str) -> None:
    """Der Wert ist jeweils ein **gueltiger** - abgewiesen wird also der Weg und
    nicht der Inhalt. Genau darauf kommt es an: sonst liesse sich die Sperre mit
    einem Wert umgehen, den die Regeln zufaellig auch akzeptiert haetten.
    """
    with pytest.raises(AssertionError):
        bauen(rohwert, key=ConstructionKey())


def test_ein_fremder_schluessel_wird_auch_bei_der_identitaet_abgewiesen() -> None:
    """Beleg: `UserId` traegt eine UUID statt eines Strings - und sperrt genauso."""
    with pytest.raises(AssertionError):
        UserId(uuid7(), key=ConstructionKey())


def test_die_factories_bauen_weiterhin() -> None:
    """Beleg: der eine offene Weg bleibt offen - sonst waere die Sperre wertlos."""
    assert DisplayName.hydrate("Markus").value == "Markus"
    assert Password.hydrate("geheim-genug-fuer-alle").value == "geheim-genug-fuer-alle"
    assert PasswordHash.hydrate("$argon2id$v=19$...").value == "$argon2id$v=19$..."
    assert UserTimeZone.hydrate("Europe/Berlin").value == "Europe/Berlin"
    idn = IdnEncoderAdapter(PassthroughIdnLabels())
    assert Email.hydrate("Markus@Example.de", idn).value == "markus@example.de"
    assert UserId.generate() != UserId.generate()
