"""Was die Geltungsdauer selbst beantwortet.

**Nicht**, ob eine Dauer zulaessig ist - das entscheidet die Konfiguration des
Prozesses und wird in `tests/test_settings.py` geprueft.
"""

from src.contexts.identity.domain import TokenLifetime
from src.contexts.shared_kernel import Timestamp


def test_der_ablauf_wird_an_einer_stelle_gerechnet() -> None:
    assert TokenLifetime.hydrate(60).expires_from(Timestamp(1798221600)) == Timestamp(1798221660)
