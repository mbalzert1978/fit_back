"""Domain-Port UserRegistry - der Nutzerbestand, der die E-Mail-Eindeutigkeit haelt."""

from typing import Protocol

from src.contexts.identity.domain.entities.user import User
from src.contexts.identity.domain.errors import EmailAlreadyRegistered
from src.contexts.shared_kernel import AsyncResult

__all__ = ["UserRegistry", "UserRegistryError"]


type UserRegistryError = EmailAlreadyRegistered
"""Die **erwarteten** Ausgaenge dieses Ports - heute genau einer.

Eigene Union statt Sammeltyp, und sie waechst nur mit dem, was ein Adapter
tatsaechlich als Wert meldet - nicht auf Verdacht:
docs/decisions/2026-08-17-0933-fehler-union-je-port-statt-domainerror-als-sammeltyp.md.
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
