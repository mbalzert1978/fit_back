"""In-Memory-Ablage der Refresh-Token: deterministisch, ohne Hash-Verfahren."""

from dataclasses import dataclass, field
from typing import Final, final

from src.contexts.identity.application.register_user.abstractions import (
    MintedSecret,
    RefreshTokenRecord,
)

__all__ = ["InMemorySessionTokens", "IssuedRefreshToken"]

_HASH_PREFIX: Final = "fake-hash-of-"
"""Ein umkehrbarer "Abdruck" - genau deshalb erkennbar unecht.

Die Produktion legt SHA-256 ab und kaeme nie an den Klartext zurueck. Der Fake
muss es koennen: die Test-API zeigt den abgelegten Token, damit ein Spec ihn
gegen den ausgegebenen halten kann.
"""


@final
@dataclass(frozen=True, slots=True)
class IssuedRefreshToken:
    """Ein abgelegter Refresh-Token, wie ein Spec ihn zu sehen bekommt.

    Ein eigener Typ und kein `tuple[str, str]`: wer die beiden Werte vertauscht,
    soll es am Namen merken und nicht an einem roten Test drei Zeilen spaeter.
    """

    user_id: str
    token: str = field(repr=False)


@final
class InMemorySessionTokens:
    """Erfuellt `RegisterUserSessionTokens` fuer Specs.

    Merkt sich, was abgelegt wurde - in der Produktion ist das eine
    Datenbankzeile, hier eine Liste, und in beiden Faellen nachprueftbar.
    """

    def __init__(self) -> None:
        """Starte ohne ausgestellten Token."""
        self.issued: list[IssuedRefreshToken] = []
        """Je Ablage ein Eintrag - in der Reihenfolge des Ausstellens."""

        self._minted = 0
        """Wie viele Geheimnisse schon herausgegeben wurden - haelt sie unterscheidbar."""

    def mint_secret(self) -> MintedSecret:
        """Gib ein erkennbar unechtes Geheimnis heraus."""
        self._minted += 1
        plaintext = f"fake-refresh-{self._minted}"
        return MintedSecret(plaintext=plaintext, hashed=f"{_HASH_PREFIX}{plaintext}")

    async def store(self, record: RefreshTokenRecord) -> None:
        """Lege die Zeile ab - festgehalten wird der Klartext hinter dem Abdruck."""
        self.issued.append(
            IssuedRefreshToken(
                user_id=record.user_id,
                token=record.token_hash.removeprefix(_HASH_PREFIX),
            )
        )
