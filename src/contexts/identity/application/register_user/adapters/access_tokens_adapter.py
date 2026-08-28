"""Implementiert den Domain-Port `AccessTokens` ueber die public Naht.

Uebersetzt und sonst nichts: die Domaene nennt Nutzer, Zeitpunkt und Dauer, die
Naht will drei Primitive. Das Ende des Fensters rechnet `TokenLifetime` aus -
hier wird nichts ausgerechnet.
"""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RegisterUserAccessTokens,
)
from src.contexts.identity.domain import Grant, TokenLifetime, UserId
from src.contexts.shared_kernel import Timestamp

__all__ = ["AccessTokensAdapter"]


@final
class AccessTokensAdapter:
    """Faltet die Signatur-Anfrage der Domaene auf die Naht."""

    def __init__(self, access_tokens: RegisterUserAccessTokens) -> None:
        """Nimm den Signierer entgegen (Fake oder Produktion)."""
        self._access_tokens = access_tokens

    def sign(self, user_id: UserId, issued_at: Timestamp, lifetime: TokenLifetime) -> Grant:
        """Signiere den Token und paare ihn mit der Dauer, die das Fenster aufspannt."""
        return Grant.hydrate(
            self._access_tokens.sign(
                str(user_id),
                issued_at.unix_seconds,
                lifetime.expires_from(issued_at).unix_seconds,
            ),
            lifetime,
        )
