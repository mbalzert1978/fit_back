"""Domain-Port TokenSecrets - die Quelle frischer Geheimnisse.

Bewusst **schmal**: genau eine Operation, weil genau sie in eine Aggregat-
Methode hineingereicht wird. `RefreshToken.issue` bekommt diesen Port und zieht
sich sein Geheimnis selbst
(docs/decisions/2026-08-28-0930-das-aggregat-zieht-sein-geheimnis-selbst.md).
"""

from typing import Protocol

from src.contexts.identity.domain.value_objects.token_secret import TokenSecret

__all__ = ["TokenSecrets"]


class TokenSecrets(Protocol):
    """Zieht ein frisches Geheimnis und bildet dessen Abdruck.

    Bewusst **nicht** fallibel deklariert: ein Zufallsgenerator, der nichts
    hergibt, ist ein Betriebsfall und kein Fachfall
    (.rules/python/python-error-handling.md).
    """

    def mint(self) -> TokenSecret:
        """Gib ein frisches Geheimnis heraus - Klartext und Abdruck in einem Zug."""
        ...
