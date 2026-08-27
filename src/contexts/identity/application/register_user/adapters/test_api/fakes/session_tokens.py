"""In-Memory-Sitzungsausstellung: deterministisch, ohne Signaturverfahren."""

from typing import Final, final

from src.contexts.identity.application.register_user.abstractions import (
    MintedSecret,
    RefreshTokenRecord,
)

__all__ = ["InMemorySessionTokens"]

_HASH_PREFIX: Final = "fake-hash-of-"
"""Ein umkehrbarer "Abdruck" - genau deshalb erkennbar unecht.

Die Produktion legt SHA-256 ab und kaeme nie an den Klartext zurueck. Der Fake
muss es koennen: die Test-API zeigt den abgelegten Token, damit ein Spec ihn
gegen den ausgegebenen halten kann.
"""


@final
class InMemorySessionTokens:
    """Erfuellt `RegisterUserSessionTokens` fuer Specs.

    Merkt sich, was abgelegt wurde - in der Produktion ist das eine
    Datenbankzeile, hier eine Liste, und in beiden Faellen nachprueftbar.
    """

    def __init__(self) -> None:
        """Starte ohne ausgestellten Token."""
        self.issued: list[tuple[str, str]] = []
        """Je Ablage `(user_id, token)` - in der Reihenfolge des Ausstellens."""

        self._minted = 0
        """Wie viele Geheimnisse schon herausgegeben wurden - haelt sie unterscheidbar."""

    def mint_secret(self) -> MintedSecret:
        """Gib ein erkennbar unechtes Geheimnis heraus."""
        self._minted += 1
        plaintext = f"fake-refresh-{self._minted}"
        return MintedSecret(plaintext=plaintext, hashed=f"{_HASH_PREFIX}{plaintext}")

    async def store(self, record: RefreshTokenRecord) -> None:
        """Lege die Zeile ab - festgehalten wird der Klartext hinter dem Abdruck."""
        self.issued.append((record.user_id, record.token_hash.removeprefix(_HASH_PREFIX)))

    def sign_access_token(self, user_id: str, issued_at: int, expires_at: int) -> str:
        """Gib ein erkennbar unechtes Access-Token heraus."""
        return f"fake-access-{user_id}-{issued_at}-{expires_at}"
