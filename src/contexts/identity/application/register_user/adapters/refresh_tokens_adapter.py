"""Implementiert den Domain-Port `RefreshTokens` ueber die public Naht.

Uebersetzt und sonst nichts: Aggregat rein, flache Zeile raus. Der Ablauf steht
im Handler.
"""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RefreshTokenRecord,
    RegisterUserSessionTokens,
)
from src.contexts.identity.domain import RefreshToken

__all__ = ["RefreshTokensAdapter"]


@final
class RefreshTokensAdapter:
    """Faltet das Aggregat auf die Zeile der Ablage."""

    def __init__(self, sessions: RegisterUserSessionTokens) -> None:
        """Nimm die Ablage entgegen (Fake oder Produktion)."""
        self._sessions = sessions

    async def store(self, token: RefreshToken) -> None:
        """Falte das Aggregat auf die flache Zeile und lege sie ab.

        Der Klartext steht bewusst nicht darin: abgelegt wird nur der Abdruck.
        """
        await self._sessions.store(
            RefreshTokenRecord(
                token_id=str(token.id),
                user_id=str(token.user_id),
                token_hash=token.token_hash.value,
                issued_at=token.issued_at.unix_seconds,
                expires_at=token.expires_at.unix_seconds,
            )
        )
