"""Implementiert den Domain-Port `SessionIssuer` ueber die public Naht."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RefreshTokenRecord,
    RegisterUserAccessTokens,
    RegisterUserSessionTokens,
)
from src.contexts.identity.domain import (
    IssuedCredentials,
    RefreshToken,
    TokenHash,
    TokenLifetime,
    User,
)

__all__ = ["SessionIssuerAdapter"]


@final
class SessionIssuerAdapter:
    """Uebersetzt zwischen Aggregat und Naht - in beide Richtungen.

    Rechnet selbst nichts aus: den Ablauf beantwortet `TokenLifetime`, die
    Felder der Zeile das Aggregat. Der Adapter fragt beide und wickelt ihre
    Antworten auf Primitive ab - mehr ist seine Rolle nicht
    (.rules/python/python-feature-slices.md, "Handler, Adapter, Mapper sind
    verschiedene Dinge").

    Der Klartext des Geheimnisses geht an der Domaene vorbei direkt in die
    Zugangsdaten - er wird nie abgelegt.
    """

    def __init__(
        self, sessions: RegisterUserSessionTokens, access_tokens: RegisterUserAccessTokens
    ) -> None:
        """Nimm Ablage und Signierer entgegen (Fakes oder Produktion)."""
        self._sessions = sessions
        self._access_tokens = access_tokens

    async def issue(
        self, user: User, access_lifetime: TokenLifetime, refresh_lifetime: TokenLifetime
    ) -> IssuedCredentials:
        """Stelle den Refresh-Token aus, lege ihn ab und signiere den Zugang.

        Als Zeitpunkt dient `registered_at` des Aggregats - dieselbe Uhrablesung,
        aus der auch die Nutzer-Zeile entsteht.
        """
        secret = self._sessions.mint_secret()
        token = RefreshToken.issue(
            user_id=user.id,
            token_hash=TokenHash.hydrate(secret.hashed),
            issued_at=user.registered_at,
            lifetime=refresh_lifetime,
        )
        await self._sessions.store(_as_record(token))
        return IssuedCredentials.hydrate(
            access_token=self._access_tokens.sign(
                str(user.id),
                user.registered_at.unix_seconds,
                access_lifetime.expires_from(user.registered_at).unix_seconds,
            ),
            access_lifetime=access_lifetime,
            refresh_token=secret.plaintext,
            refresh_lifetime=refresh_lifetime,
        )


def _as_record(token: RefreshToken) -> RefreshTokenRecord:
    """Falte das Aggregat auf die flache Zeile der Naht."""
    return RefreshTokenRecord(
        token_id=str(token.id),
        user_id=str(token.user_id),
        token_hash=token.token_hash.value,
        issued_at=token.issued_at.unix_seconds,
        expires_at=token.expires_at.unix_seconds,
    )
