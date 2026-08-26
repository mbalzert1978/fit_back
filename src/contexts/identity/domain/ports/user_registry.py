"""Domain-Port UserRegistry - der Nutzerbestand, der die E-Mail-Eindeutigkeit haelt."""

from typing import Protocol

from src.contexts.identity.domain.entities.user import User
from src.contexts.identity.domain.errors import EmailAlreadyRegistered
from src.contexts.shared_kernel import AsyncResult

__all__ = ["UserRegistry", "UserRegistryError"]


type UserRegistryError = EmailAlreadyRegistered
"""Die **erwarteten** Ausgaenge dieses Ports - heute genau einer.

Eine eigene Union je Port statt eines Sammeltyps ueber den ganzen Context: nur so
zaehlt die Aufzaehlung ehrlich auf, was hier ankommen kann, und nur so bleibt ein
`match` darueber eine Aussage statt einer Pflichtuebung ueber zwei Dutzend
Faelle, von denen einer eintritt.

Sie waechst mit dem, was der Adapter als Wert melden **kann**: erwartete
IO-Ausgaenge gehoeren dann hierher (als Fall im `Result`, nicht als Exception),
Unerwartetes bubbelt weiterhin hoch. Sie waechst nicht auf Verdacht - ein Fall
ohne Adapter, der ihn liefert, ist ein Arm, den niemand erreicht.
"""


class UserRegistry(Protocol):
    """Von der Domaene vorgegebener Port - spricht ausschliesslich Value Objects.

    **Eine** Operation, bewusst. Ein vorgelagertes "ist die E-Mail noch frei?"
    waere eine Auskunft, die im Moment ihrer Beantwortung schon veraltet sein
    kann: zwischen Pruefung und Schreiben passt jeder nebenlaeufige Vorgang. Die
    Eindeutigkeit entscheidet die Instanz, die sie auch durchsetzt - der
    Unique-Index -, und `add` meldet deren Urteil zurueck.
    """

    def add(self, user: User) -> AsyncResult[User, UserRegistryError]:
        """Nimm den User auf; `Err(EmailAlreadyRegistered)`, wenn die E-Mail vergeben ist."""
        ...
