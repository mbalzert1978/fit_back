"""Die Domaenen-Operation hinter dem Use Case RegisterUser.

Eine Registrierung erzeugt die Aggregatwurzel erst - es gibt also keine Wurzel,
an der die Operation als Methode haengen koennte. Deshalb steht sie hier als
Modul-Funktion der Domaene und nicht als Handler-Logik: die Reihenfolge
"E-Mail beanspruchen, dann aufnehmen" ist eine Fachregel, keine Orchestrierung.
"""

from src.contexts.identity.domain.entities.user import User
from src.contexts.identity.domain.errors import DomainError
from src.contexts.identity.domain.ports.user_registry import UserRegistry
from src.shared_kernel import Err, Ok, Result

__all__ = ["complete_registration"]


async def complete_registration(
    registry: UserRegistry,
    candidate: User,
) -> Result[User, DomainError]:
    """Beanspruche die E-Mail des Kandidaten und nimm ihn in die Registry auf.

    Fail-fast: scheitert schon der Anspruch auf die E-Mail, wird gar nicht erst
    geschrieben. Der zweite Fehlschlag (`add`) deckt das Wettrennen ab, bei dem
    zwischen Pruefung und Schreiben ein anderer Vorgang dieselbe E-Mail belegt.
    """
    match await registry.claim_email(candidate.email):
        case Err() as already_taken:
            return already_taken
        case Ok():
            return await registry.add(candidate)
