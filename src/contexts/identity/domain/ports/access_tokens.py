"""Domain-Port AccessTokens - das Signaturverfahren selbst lebt ausserhalb."""

from typing import Protocol

from src.contexts.identity.domain.value_objects.credentials import Grant
from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.shared_kernel import Timestamp

__all__ = ["AccessTokens"]


class AccessTokens(Protocol):
    """Signiert den Access-Token eines Nutzers und gibt ihn als Ausgabe heraus.

    Gibt einen `Grant` zurueck und keinen `str`: der signierte Token ist fuer die
    Domaene undurchsichtig, aber ohne seine Geltungsdauer unbrauchbar. Wer
    signiert, kennt die Dauer bereits - er paart beide, statt den Aufrufer
    paaren zu lassen.

    Bewusst **nicht** fallibel deklariert: eine fehlschlagende Signatur ist ein
    Konfigurationsfehler, kein erwarteter Fachfall.
    """

    def sign(self, user_id: UserId, issued_at: Timestamp, lifetime: TokenLifetime) -> Grant:
        """Signiere den Token fuer das Fenster, das diese Dauer aufspannt."""
        ...
