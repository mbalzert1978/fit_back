"""Die Zuordnung der `DomainError`-Faelle im Response-Mapper von RegisterUser.

Geprueft wird die **Struktur** der Zuordnung, nicht das Verhalten jedes Arms - und
das hat einen Grund, den man kennen muss, bevor man diesen Test erweitert:

`RegisterUserPipeline.run` validiert zuerst und schickt Feldfehler direkt in
`to_invalid_response`. Zu `to_response` gelangt nur der zweite Weg, und dort baut
`to_command` mit `hydrate` (infallibel), sodass die Fehlerhaelfte des `Result` allein
`EmailAlreadyRegistered` tragen kann. **Die uebrigen Arme von `to_response` sind auf
dem Produktionspfad unerreichbar.** Sie zu testen hiesse, Eingaben von Hand
herzustellen, die der laufende Code nicht erzeugen kann - ein gruener Test ueber
Fiktion.

Was hier bleibt, ist deshalb das, was auch ohne diese Arme wahr sein muss: dass jeder
Fall der Union zugeordnet ist, dass jeder veroeffentlichte einen Code traegt, und dass
die beiden Faelle ohne Code laut scheitern statt dem Aufrufer die Schuld zu geben.

Die unerreichbaren Arme verschwinden mit Stufe 4 von Ticket 0011 (echte Pipeline statt
Wrapper mit `if`); danach hat `to_response` vier Arme, die alle vorkommen koennen.

Regel: `.rules/python/python-error-handling.md`, "Jeder `match` ist vollstaendig".
"""

import pytest

from src.contexts.identity.application.register_user.adapters import IdnEncoderAdapter
from src.contexts.identity.application.register_user.fakes import PassthroughIdnLabels
from src.contexts.identity.application.register_user.mappers.register_user_response_mapper import (
    to_response,
)
from src.contexts.identity.application.register_user.response import EmailAlreadyTaken
from src.contexts.identity.domain import (
    DomainError,
    Email,
    EmailAlreadyRegistered,
    PasswordHashIsEmpty,
    UserIdMalformed,
)
from src.contexts.shared_kernel import Err
from src.contexts.shared_kernel.coded_error import error_cases

SCHEITERT_LAUT = {PasswordHashIsEmpty, UserIdMalformed}
"""Faelle ohne Fehlercode.

Sie stammen aus dem Hasher und aus `UserId.generate()`, nicht aus der Anfrage - es gibt
keine Antwort, die dem Aufrufer etwas Wahres ueber sein eigenes Zutun sagen koennte.
"""

KOLLISION = {EmailAlreadyRegistered}
"""Eigener Ausgang mit eigenem Statuscode, kein Feldfehler.

Traegt selbst keinen Code: veroeffentlicht wird `EmailAlreadyTaken`, und ein Code
gehoert laut `shared_kernel/coded_error.py` genau einmal an genau einen Fall.
"""

FELDFEHLER = set(error_cases(DomainError)) - SCHEITERT_LAUT - KOLLISION
"""Alles Uebrige - vom Mapper auf Feld, Code und Parameter abgebildet."""


def test_jeder_domaenenfehler_ist_zugeordnet() -> None:
    """Kein Fall darf zwischen den Mengen hindurchfallen.

    Waechst `DomainError`, wird dieser Test rot und verlangt die Entscheidung, wohin
    der neue Fall gehoert - statt dass er stillschweigend in einem Arm verschwindet.
    """
    assert FELDFEHLER | KOLLISION | SCHEITERT_LAUT == set(error_cases(DomainError))
    assert not (FELDFEHLER & KOLLISION)
    assert not (FELDFEHLER & SCHEITERT_LAUT)


@pytest.mark.parametrize(
    "case", sorted(FELDFEHLER, key=lambda c: c.__name__), ids=lambda c: c.__name__
)
def test_jeder_feldfehler_traegt_einen_code(case: type) -> None:
    """Ohne Code gaebe es am HTTP-Rand keinen Text zu rendern."""
    assert isinstance(getattr(case, "code", None), str)
    assert case.code, f"{case.__name__} traegt einen leeren Code"


@pytest.mark.parametrize(
    "case", sorted(SCHEITERT_LAUT, key=lambda c: c.__name__), ids=lambda c: c.__name__
)
def test_ein_fall_ohne_code_traegt_wirklich_keinen(case: type) -> None:
    """Die Zuordnung oben ist nur richtig, solange das stimmt."""
    assert not hasattr(case, "code"), (
        f"{case.__name__} traegt einen Code und gehoert dann zu FELDFEHLER."
    )


def test_die_email_kollision_wird_nicht_zum_feldfehler() -> None:
    """Der eine Fehlerfall, der `to_response` tatsaechlich erreicht."""
    email = Email.hydrate("besetzt@example.com", IdnEncoderAdapter(PassthroughIdnLabels()))

    antwort = to_response(Err(EmailAlreadyRegistered(email)))

    assert antwort == EmailAlreadyTaken("besetzt@example.com")
