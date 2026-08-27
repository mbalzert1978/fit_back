"""Domain-Port SessionIssuer - das Signieren und Ablegen lebt ausserhalb."""

from typing import Protocol

from src.contexts.identity.domain.entities.user import User
from src.contexts.identity.domain.value_objects.issued_credentials import IssuedCredentials

__all__ = ["SessionIssuer"]


class SessionIssuer(Protocol):
    """Stellt einem aufgenommenen User seine Zugangsdaten aus.

    Bewusst **nicht** fallibel deklariert - wie `PasswordHasher` und aus
    demselben Grund: es gibt keinen *erwarteten* Fehlschlag. Eine tote Datenbank
    ist ein Betriebsfall und keine Fachentscheidung; sie faellt als Exception bis
    zur Middleware durch (.rules/python/python-error-handling.md).

    Ein halb ausgestellter Zustand kann dabei nicht entstehen: Nutzer-Zeile,
    Refresh-Token und Ereignis haengen in **derselben** Transaktion
    (`src/api/composition.py`, `request_transaction`). Bricht die Ausstellung ab,
    wird nichts committet - auch der Nutzer nicht.
    """

    async def issue(
        self, user: User, access_token_seconds: int, refresh_token_seconds: int
    ) -> IssuedCredentials:
        """Stelle die Zugangsdaten des aufgenommenen Users aus.

        Die beiden Geltungsdauern kommen als Primitive herein: sie sind
        Konfiguration des Prozesses, kein Wissen der Domaene.
        """
        ...
