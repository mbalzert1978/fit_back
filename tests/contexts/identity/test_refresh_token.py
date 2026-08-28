"""Was das Aggregat `RefreshToken` selbst entscheidet."""

from typing import final

from src.contexts.identity.domain import (
    RefreshToken,
    RefreshTokenIssuance,
    TokenLifetime,
    TokenSecret,
    UserId,
)
from src.contexts.shared_kernel import Timestamp

AUSGESTELLT_AM = Timestamp(1798221600)


@final
class StubTokenSecrets:
    """Gibt immer dasselbe Geheimnis heraus."""

    def mint(self) -> TokenSecret:
        return TokenSecret.hydrate("ein-klartext", "ein-abdruck")


def _stelle_aus() -> RefreshTokenIssuance:
    return RefreshToken.issue(
        user_id=UserId.generate(),
        secrets=StubTokenSecrets(),
        issued_at=AUSGESTELLT_AM,
        lifetime=TokenLifetime.hydrate(3_600),
    )


def test_der_ablauf_liegt_die_geltungsdauer_hinter_der_ausstellung() -> None:
    token = _stelle_aus().refresh_token

    assert token.issued_at == AUSGESTELLT_AM
    assert token.expires_at == Timestamp(AUSGESTELLT_AM.unix_seconds + 3_600)


def test_das_aggregat_behaelt_den_abdruck_und_gibt_den_klartext_heraus() -> None:
    issuance = _stelle_aus()

    assert issuance.refresh_token.token_hash.value == "ein-abdruck"
    assert issuance.grant.token == "ein-klartext"


def test_die_ausgabe_traegt_die_geltungsdauer_des_abgelegten_token() -> None:
    issuance = _stelle_aus()

    assert issuance.grant.lifetime.seconds == 3_600
