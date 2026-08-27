"""Was das Aggregat `RefreshToken` selbst entscheidet."""

from src.contexts.identity.domain import RefreshToken, TokenHash, TokenLifetime, UserId
from src.contexts.shared_kernel import Timestamp

AUSGESTELLT_AM = Timestamp(1798221600)


def test_der_ablauf_liegt_die_geltungsdauer_hinter_der_ausstellung() -> None:
    token = RefreshToken.issue(
        user_id=UserId.generate(),
        token_hash=TokenHash.hydrate("ein-abdruck"),
        issued_at=AUSGESTELLT_AM,
        lifetime=TokenLifetime.refresh(3_600),
    )

    assert token.issued_at == AUSGESTELLT_AM
    assert token.expires_at == Timestamp(AUSGESTELLT_AM.unix_seconds + 3_600)
    assert token.lifetime_seconds == 3_600
