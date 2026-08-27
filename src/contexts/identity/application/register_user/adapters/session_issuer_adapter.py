"""Implementiert den Domain-Port `SessionIssuer` ueber die public Naht."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RefreshTokenRecord,
    RegisterUserSessionTokens,
)
from src.contexts.identity.domain import (
    IssuedCredentials,
    RefreshToken,
    TokenHash,
    User,
)

__all__ = ["SessionIssuerAdapter"]


@final
class SessionIssuerAdapter:
    """Uebersetzt zwischen Aggregat und Naht - in beide Richtungen.

    Das Aggregat entsteht in der Domaene (`RefreshToken.issue`), die Zeile
    entsteht hier, und der Klartext des Geheimnisses geht an der Domaene vorbei
    direkt in die Zugangsdaten - er wird nie abgelegt.
    """

    def __init__(self, sessions: RegisterUserSessionTokens) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder Aussteller)."""
        self._sessions = sessions

    async def issue(
        self, user: User, access_token_seconds: int, refresh_token_seconds: int
    ) -> IssuedCredentials:
        """Stelle den Refresh-Token aus, lege ihn ab und signiere den Zugang.

        Als Zeitpunkt dient `registered_at` des Aggregats. Das ist dieselbe
        Uhrablesung, aus der auch die Nutzer-Zeile entsteht; eine zweite liesse
        Konto und Token auseinanderliegen, ohne dass jemand davon etwas haette.
        """
        secret = self._sessions.mint_secret()
        token = RefreshToken.issue(
            user_id=user.id,
            token_hash=TokenHash.hydrate(secret.hashed),
            issued_at=user.registered_at,
            lifetime_seconds=refresh_token_seconds,
        )
        await self._sessions.store(_as_record(token))
        return IssuedCredentials.hydrate(
            access_token=self._sessions.sign_access_token(
                str(user.id),
                user.registered_at.unix_seconds,
                user.registered_at.unix_seconds + access_token_seconds,
            ),
            expires_in=access_token_seconds,
            refresh_token=secret.plaintext,
            refresh_expires_in=token.lifetime_seconds,
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
