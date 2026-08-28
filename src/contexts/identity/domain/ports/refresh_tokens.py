"""Domain-Port RefreshTokens - Geheimnis-Quelle und Ablage des Aggregats.

Erbt `TokenSecrets`, weil es **ein** Mitspieler ist: in der Produktion
`PostgresSessionTokens`, in Specs `InMemorySessionTokens`. Zwei Vertraege waeren
zwei Mitspieler, und der zweite existiert nicht
(.rules/python/python-feature-slices.md).

Getrennt gelesen wird trotzdem: `RefreshToken.issue` verlangt nur `TokenSecrets`
und bekommt damit kein `store` in die Hand
(docs/decisions/2026-08-28-0930-das-aggregat-zieht-sein-geheimnis-selbst.md).
"""

from typing import Protocol

from src.contexts.identity.domain.entities.refresh_token import RefreshToken
from src.contexts.identity.domain.ports.token_secrets import TokenSecrets

__all__ = ["RefreshTokens"]


class RefreshTokens(TokenSecrets, Protocol):
    """Stellt Geheimnisse aus und legt ausgestellte Token ab."""

    async def store(self, token: RefreshToken) -> None:
        """Lege das ausgestellte Aggregat ab.

        Nimmt das Aggregat und keine flache Zeile: **welche** Felder ein
        Refresh-Token traegt, entscheidet die Domaene; wie sie in eine Zeile
        fallen, der Adapter.

        Kein Ergebnistyp: die Id ist frisch, der Abdruck eindeutig - was hier
        schiefgeht, ist ein Betriebsfall und faellt bis zur Middleware durch.
        """
        ...
