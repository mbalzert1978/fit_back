"""Provider-Verifikation gegen den Identity-Vertrag des Frontends (Ticket #94).

Der Pact unter `contracts/pacts/identity/` ist die Vorgabe der HTTP-Grenze
(`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`).

**Der Lauf gegen ihn ist erwartungsgemaess rot**, solange
`POST /api/v1/identity/register` ihn nicht erfuellt. Ein Pact vom Konsumenten ist
Vorgabe, nicht Nachweis - rot heisst hier "noch nicht gebaut", nicht "falsch
getestet". Gruen wird er mit dem Ticket, das den Endpunkt heranbaut.

Weil ein roter Lauf nichts belegen kann, laeuft die **Mechanik** gegen einen
zweiten, kleinen Pact, dessen Konsument dieses Repo selbst ist: derselbe Weg,
dieselbe Verdrahtung, aber gruen. Er belegt, was das Ticket verlangt - zwei
Interaktionen mit demselben State stoeren einander nicht.

Nur die fuenf `register`-Interaktionen laufen mit; `login`, `refresh`, `logout`
und `me` sind noch nicht gebaut und bleiben ueber `REGISTER_PFAD` draussen, bis
ihr jeweiliges Ticket kommt. Die Mechanik dahinter steht in
`provider_verification.py`, die beiden Pacts und die `Ablage` reicht die
`conftest.py` herein - dieses Modul oeffnet keine Datei.
"""

from pathlib import PurePosixPath

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from src.main import app
from tests.contracts.provider_verification import Ablage, Pact, ProviderVerifikation
from tests.contracts.testkonto import Testkonto

PROVIDER = "nutritrack-identity"

REGISTER_PFAD = PurePosixPath("/api/v1/identity/register")
"""Der eine Endpunkt, der heute gebaut ist - und damit der einzige, der mitlaeuft.

Ein weiterer kostet eine Zeile hier und die States, die seine Interaktionen
tragen; welche Interaktionen das sind, liest der Builder aus dem Pact.
"""

# Die States benennen ihr Konto im Klartext, statt es als V3-`parameters` zu
# fuehren - hier steht deshalb, was dort im Text steht.
EMAIL = "a@b.de"
PASSWORT = "geheim123"
KEIN_KONTO = f"Keine Registrierung mit {EMAIL} vorhanden"
KONTO_EXISTIERT = f"Nutzer {EMAIL} existiert mit Passwort {PASSWORT}"

pytestmark = pytest.mark.asyncio


async def test_die_registrierung_erfuellt_den_identity_vertrag(
    postgres_engine: AsyncEngine,
    identity_pact: Pact,
    pact_ablage: Ablage,
) -> None:
    """Spiele die fuenf register-Interaktionen gegen die laufende App ab."""
    konto = Testkonto(postgres_engine, email=EMAIL, passwort=PASSWORT)

    await (
        ProviderVerifikation.fuer(PROVIDER, identity_pact)
        .nur_pfade(REGISTER_PFAD)
        .mit_state(KEIN_KONTO, setup=konto.entfernen, teardown=konto.entfernen)
        .mit_state(KONTO_EXISTIERT, setup=konto.anlegen, teardown=konto.entfernen)
        .verifiziere(app, pact_ablage)
    )


async def test_zwei_interaktionen_mit_demselben_state_stoeren_einander_nicht(
    postgres_engine: AsyncEngine,
    mechanik_pact: Pact,
    pact_ablage: Ablage,
) -> None:
    """Derselbe anlegende State, zweimal hintereinander - beide Male durch.

    Bleibt das Konto der ersten Interaktion stehen, laeuft das Setup der zweiten
    in den `uq_users_email` und der Lauf wird rot. `Testkonto.anlegen()` raeumt
    bewusst nicht selbst vor, damit dieser Fall wirklich eintritt statt verdeckt
    zu werden.
    """
    konto = Testkonto(postgres_engine, email=EMAIL, passwort=PASSWORT)

    await (
        ProviderVerifikation.fuer(PROVIDER, mechanik_pact)
        .mit_state(KONTO_EXISTIERT, setup=konto.anlegen, teardown=konto.entfernen)
        .verifiziere(app, pact_ablage)
    )
