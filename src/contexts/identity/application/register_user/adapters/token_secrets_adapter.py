"""Implementiert den Domain-Port `TokenSecrets` ueber die public Naht.

Uebersetzt und sonst nichts: die Naht gibt zwei Primitive, die Domaene will ein
gepaartes Value Object.
"""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RegisterUserSessionTokens,
)
from src.contexts.identity.domain import TokenSecret

__all__ = ["TokenSecretsAdapter"]


@final
class TokenSecretsAdapter:
    """Faltet das frische Geheimnis der Naht auf den Domaenentyp."""

    def __init__(self, sessions: RegisterUserSessionTokens) -> None:
        """Nimm die Geheimnis-Quelle entgegen (Fake oder Produktion)."""
        self._sessions = sessions

    def mint(self) -> TokenSecret:
        """Hole ein frisches Geheimnis und falte es auf den Domaenentyp."""
        minted = self._sessions.mint_secret()
        return TokenSecret.hydrate(minted.plaintext, minted.hashed)
