"""Domain-Port AccessTokens - das Signaturverfahren selbst lebt ausserhalb."""

from typing import Protocol

from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.shared_kernel import Timestamp

__all__ = ["AccessTokens"]


class AccessTokens(Protocol):
    """Signiert den Access-Token eines Nutzers.

    Gibt einen `str` zurueck und kein Value Object: der signierte Token traegt
    keine Regel, wird nie wiedergelesen und ist fuer die Domaene undurchsichtig.
    Er wird sofort mit seiner Geltungsdauer gepaart - das tut `Grant` im Slice.

    Bewusst **nicht** fallibel deklariert: eine fehlschlagende Signatur ist ein
    Konfigurationsfehler, kein erwarteter Fachfall.
    """

    def sign(self, user_id: UserId, issued_at: Timestamp, lifetime: TokenLifetime) -> str:
        """Signiere den Token fuer das Fenster, das diese Dauer aufspannt."""
        ...
