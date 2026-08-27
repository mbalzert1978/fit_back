"""Das Fenster, in dem eine Geltungsdauer liegen darf.

Kein Fachfall, sondern eine falsch gesetzte Konfiguration - also eine Exception.
"""

import pytest

from src.contexts.identity.domain import (
    ACCESS_TOKEN_MAXIMUM_SECONDS,
    REFRESH_TOKEN_MAXIMUM_SECONDS,
    TokenLifetime,
)
from src.contexts.shared_kernel import Timestamp


@pytest.mark.parametrize("seconds", [0, -1])
def test_eine_geltungsdauer_ohne_dauer_wird_abgewiesen(seconds: int) -> None:
    with pytest.raises(ValueError, match="Token lifetime must be between"):
        TokenLifetime.access(seconds)


def test_der_access_token_darf_die_zusage_aus_backend_md_nicht_ueberschreiten() -> None:
    grenze = TokenLifetime.access(ACCESS_TOKEN_MAXIMUM_SECONDS)
    assert grenze.seconds == ACCESS_TOKEN_MAXIMUM_SECONDS

    with pytest.raises(ValueError, match="Token lifetime must be between"):
        TokenLifetime.access(ACCESS_TOKEN_MAXIMUM_SECONDS + 1)


def test_der_refresh_token_darf_die_zusage_aus_backend_md_nicht_ueberschreiten() -> None:
    grenze = TokenLifetime.refresh(REFRESH_TOKEN_MAXIMUM_SECONDS)
    assert grenze.seconds == REFRESH_TOKEN_MAXIMUM_SECONDS

    with pytest.raises(ValueError, match="Token lifetime must be between"):
        TokenLifetime.refresh(REFRESH_TOKEN_MAXIMUM_SECONDS + 1)


def test_der_ablauf_wird_an_einer_stelle_gerechnet() -> None:
    assert TokenLifetime.access(60).expires_from(Timestamp(1798221600)) == Timestamp(1798221660)
