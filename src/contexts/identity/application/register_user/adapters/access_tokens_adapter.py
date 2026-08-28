"""Implementiert den Domain-Port `AccessTokens` ueber die public Naht.

Uebersetzt und sonst nichts: die Domaene nennt Nutzer, Zeitpunkt und Dauer, die
Naht will drei Primitive. Das Ende des Fensters rechnet `TokenLifetime` aus -
hier wird nichts ausgerechnet.
"""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RegisterUserAccessTokens,
)
from src.contexts.identity.domain import TokenLifetime, UserId
from src.contexts.shared_kernel import Timestamp

__all__ = ["AccessTokensAdapter"]


@final
class AccessTokensAdapter:
    """Faltet die Signatur-Anfrage der Domaene auf die Naht."""

    def __init__(self, access_tokens: RegisterUserAccessTokens) -> None:
        """Nimm den Signierer entgegen (Fake oder Produktion)."""
        self._access_tokens = access_tokens

    def sign(self, user_id: UserId, issued_at: Timestamp, lifetime: TokenLifetime) -> str:
        """Signiere den Token fuer das Fenster, das diese Dauer aufspannt."""
        return self._access_tokens.sign(
            str(user_id),
            issued_at.unix_seconds,
            lifetime.expires_from(issued_at).unix_seconds,
        )
