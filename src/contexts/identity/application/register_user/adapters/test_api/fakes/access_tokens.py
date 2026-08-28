"""Erkennbar unechte Access-Token fuer Specs - ohne Signaturverfahren."""

from typing import final

__all__ = ["DeterministicAccessTokens"]


@final
class DeterministicAccessTokens:
    """Erfuellt `RegisterUserAccessTokens` mit einem lesbaren Platzhalter.

    Baut JWT **nicht** nach: was ein signiertes Token wirklich traegt, prueft
    `tests/contexts/identity/test_access_tokens.py` gegen die echte Bibliothek
    (.rules/python/python-feature-slices.md, "Fremde Bibliotheken werden nicht
    mitgetestet").
    """

    def sign(self, user_id: str, issued_at: int, expires_at: int) -> str:
        """Gib ein erkennbar unechtes Access-Token heraus."""
        return f"fake-access-{user_id}-{issued_at}-{expires_at}"
