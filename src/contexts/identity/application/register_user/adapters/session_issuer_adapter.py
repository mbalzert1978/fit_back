"""Implementiert den Domain-Port `SessionIssuer` ueber die public Naht."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RegisterUserSessionTokens,
)
from src.contexts.identity.domain import Session, User

__all__ = ["SessionIssuerAdapter"]


@final
class SessionIssuerAdapter:
    """Uebersetzt Aggregat -> Primitive und die Naht-Antwort -> `Session`."""

    def __init__(self, sessions: RegisterUserSessionTokens) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder Signierer)."""
        self._sessions = sessions

    async def issue(self, user: User) -> Session:
        """Lass die Sitzung ausstellen und hole ihre Werte nach innen.

        Als Zeitpunkt geht `registered_at` des Aggregats ueber die Naht. Das ist
        dieselbe Uhrablesung, aus der auch die Nutzer-Zeile entsteht; eine
        zweite liesse Konto und Token um Millisekunden auseinanderliegen, ohne
        dass jemand davon etwas haette.
        """
        issued = await self._sessions.issue(str(user.id), user.registered_at.unix_seconds)
        return Session.hydrate(
            access_token=issued.access_token,
            expires_in=issued.expires_in,
            refresh_token=issued.refresh_token,
            refresh_expires_in=issued.refresh_expires_in,
        )
