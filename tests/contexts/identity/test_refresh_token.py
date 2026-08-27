"""Was das Aggregat `RefreshToken` selbst entscheidet.

Die Geltungsdauer kommt als Primitiv von aussen - geprueft wird sie trotzdem
hier, denn ein bereits abgelaufener Token ist kein Token.
"""

import pytest

from src.contexts.identity.domain import RefreshToken, TokenHash, UserId
from src.contexts.shared_kernel import Timestamp

AUSGESTELLT_AM = Timestamp(1798221600)


def _issue(lifetime_seconds: int) -> RefreshToken:
    return RefreshToken.issue(
        user_id=UserId.generate(),
        token_hash=TokenHash.hydrate("ein-abdruck"),
        issued_at=AUSGESTELLT_AM,
        lifetime_seconds=lifetime_seconds,
    )


def test_der_ablauf_liegt_die_geltungsdauer_hinter_der_ausstellung() -> None:
    token = _issue(3_600)

    assert token.issued_at == AUSGESTELLT_AM
    assert token.expires_at == Timestamp(AUSGESTELLT_AM.unix_seconds + 3_600)
    assert token.lifetime_seconds == 3_600


@pytest.mark.parametrize("lifetime_seconds", [0, -1])
def test_eine_geltungsdauer_ohne_dauer_wird_abgewiesen(lifetime_seconds: int) -> None:
    """Kein Fachfall, sondern eine falsch gesetzte Konfiguration - also eine Exception."""
    with pytest.raises(ValueError, match="lifetime must be positive"):
        _issue(lifetime_seconds)
