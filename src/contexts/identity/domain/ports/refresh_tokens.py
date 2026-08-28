"""Domain-Port RefreshTokens - die Ablage ausgestellter Refresh-Token.

Genau eine Operation. `TokenSecrets` steht daneben und **nicht** darueber: die
beiden Vertraege werden zwar von demselben Mitspieler erfuellt, aber von
verschiedenen Aufrufern verlangt - `RefreshToken.issue` will ziehen, der Handler
will ablegen. Ein Protocol ist strukturell; dieselbe Ablage erfuellt beide, ohne
dass einer vom anderen erbt
(docs/decisions/2026-08-28-1450-der-handler-orchestriert-die-ausstellung.md).
"""

from typing import Protocol

from src.contexts.identity.domain.entities.refresh_token import RefreshToken

__all__ = ["RefreshTokens"]


class RefreshTokens(Protocol):
    """Legt ausgestellte Refresh-Token ab."""

    async def store(self, token: RefreshToken) -> None:
        """Lege das ausgestellte Aggregat ab.

        Nimmt das Aggregat und keine flache Zeile: **welche** Felder ein
        Refresh-Token traegt, entscheidet die Domaene; wie sie in eine Zeile
        fallen, der Adapter.

        Kein Ergebnistyp: die Id ist frisch, der Abdruck eindeutig - was hier
        schiefgeht, ist ein Betriebsfall und faellt bis zur Middleware durch.
        """
        ...
