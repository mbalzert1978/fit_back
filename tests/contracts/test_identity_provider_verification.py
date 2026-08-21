"""Provider-Verifikation gegen den Identity-Vertrag des Frontends (Ticket #94).

Der Vertrag unter `contracts/pacts/identity/` ist die Vorgabe der HTTP-Grenze
(`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`).

**Dieser Lauf ist erwartungsgemaess rot**, solange
`POST /api/v1/identity/register` den Vertrag nicht erfuellt. Ein Vertrag vom
Konsumenten ist Vorgabe, nicht Nachweis - rot heisst hier "noch nicht gebaut",
nicht "falsch getestet". Gruen wird er mit dem Ticket, das den Endpunkt an den
Vertrag heranbaut.

Nur die fuenf `register`-Interaktionen laufen mit; `login`, `refresh`, `logout`
und `me` sind noch nicht gebaut und bleiben ueber `NUR_REGISTRIERUNG` draussen,
bis ihr jeweiliges Ticket kommt. Die Mechanik dahinter steht in
`provider_verification.py`.
"""

import json
import re
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from src.main import app
from tests.contracts.provider_verification import ProviderVerifikation, Zustand
from tests.contracts.testkonto import Testkonto

PROVIDER = "nutritrack-identity"
PACT_DATEI = (
    Path(__file__).parents[2] / "contracts/pacts/identity/nutritrack-app-nutritrack-identity.json"
)

NUR_REGISTRIERUNG = r"^Registrierung "
"""Die Interaktionen, die mitlaufen - als Regex auf ihre Beschreibung.

Ein weiterer Endpunkt kostet diesen Ausdruck und die States, die seine
Interaktionen tragen - keine Aenderung an der Pact-Datei.
"""

REGISTER_PFAD = "/api/v1/identity/register"

# Die States des Vertrags benennen ihr Konto im Klartext, statt es als
# V3-`parameters` zu fuehren - hier steht deshalb, was dort im Text steht.
EMAIL = "a@b.de"
PASSWORT = "geheim123"
KEIN_KONTO = f"Keine Registrierung mit {EMAIL} vorhanden"
KONTO_EXISTIERT = f"Nutzer {EMAIL} existiert mit Passwort {PASSWORT}"


@pytest.mark.asyncio
async def test_die_registrierung_erfuellt_den_identity_vertrag(
    postgres_engine: AsyncEngine,
) -> None:
    """Spiele die fuenf register-Interaktionen gegen die laufende App ab."""
    konto = Testkonto(postgres_engine, email=EMAIL, passwort=PASSWORT)

    await (
        ProviderVerifikation.fuer(PROVIDER, PACT_DATEI)
        .nur_interaktionen(NUR_REGISTRIERUNG)
        .mit_state(KEIN_KONTO, setup=konto.entfernen, teardown=konto.entfernen)
        .mit_state(KONTO_EXISTIERT, setup=konto.anlegen, teardown=konto.entfernen)
        .verifiziere(app)
    )


@pytest.mark.asyncio
async def test_zwei_interaktionen_mit_demselben_state_stoeren_einander_nicht(
    postgres_engine: AsyncEngine,
) -> None:
    """Derselbe State, zweimal hintereinander - so wie der Vertrag ihn traegt.

    Vier der fuenf Interaktionen teilen sich ihren State, und eine davon legt das
    Konto tatsaechlich an. Raeumt der Teardown nicht, laeuft der zweite `setup`
    in den `uq_users_email` und der naechste 201-Fall bekaeme 409. Hier
    ausgeloest statt behauptet: `anlegen()` raeumt nicht selbst vor.
    """
    konto = Testkonto(postgres_engine, email=EMAIL, passwort=PASSWORT)
    konto_existiert = Zustand(KONTO_EXISTIERT, setup=konto.anlegen, teardown=konto.entfernen)

    await konto_existiert.setup()  # Interaktion 1
    await konto_existiert.teardown()
    await konto_existiert.setup()  # Interaktion 2
    await konto_existiert.teardown()

    assert not await konto.existiert()


def test_ein_zustand_trennt_setup_und_teardown() -> None:
    """Pact ruft einen Handler zweimal - jeder Ruf trifft seine eigene Haelfte."""
    konto_existiert = Zustand(KONTO_EXISTIERT, setup=_nichts, teardown=_auch_nichts)

    assert konto_existiert.haelfte("setup") is _nichts
    assert konto_existiert.haelfte("teardown") is _auch_nichts


def test_der_filter_trifft_genau_die_gebauten_interaktionen() -> None:
    """Der Filter laesst die register-Interaktionen durch - und sonst keine.

    Der Ausdruck haengt an Beschreibungstexten, die der Consumer schreibt. Ohne
    diese Pruefung koennte eine Umformulierung ihn ins Leere greifen lassen: der
    Lauf waere gruen, weil er nichts mehr verifiziert.
    """
    interaktionen = json.loads(PACT_DATEI.read_text(encoding="utf-8"))["interactions"]
    muster = re.compile(NUR_REGISTRIERUNG)

    getroffen = sorted(i["description"] for i in interaktionen if muster.search(i["description"]))
    gebaut = sorted(
        i["description"] for i in interaktionen if i["request"]["path"] == REGISTER_PFAD
    )

    assert getroffen == gebaut
    assert len(getroffen) == 5


async def _nichts() -> None:
    """Platzhalter-Setup: der Test prueft die Zuordnung, nicht die Arbeit."""


async def _auch_nichts() -> None:
    """Platzhalter-Teardown, aus demselben Grund."""
