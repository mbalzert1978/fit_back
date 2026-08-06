"""Domain-Port UserRegistry - der Nutzerbestand, der die E-Mail-Eindeutigkeit haelt."""

from typing import Protocol

from src.contexts.identity.domain.entities.user import User
from src.contexts.identity.domain.errors import DomainError
from src.contexts.shared_kernel import Result

__all__ = ["UserRegistry"]


class UserRegistry(Protocol):
    """Von der Domaene vorgegebener Port - spricht ausschliesslich Value Objects.

    **Eine** Operation, bewusst. Ein vorgelagertes "ist die E-Mail noch frei?"
    waere eine Auskunft, die im Moment ihrer Beantwortung schon veraltet sein
    kann: zwischen Pruefung und Schreiben passt jeder nebenlaeufige Vorgang. Die
    Eindeutigkeit entscheidet die Instanz, die sie auch durchsetzt - der
    Unique-Index -, und `add` meldet deren Urteil zurueck.
    """

    async def add(self, user: User) -> Result[User, DomainError]:
        """Nimm den User auf; `Err(EmailAlreadyRegistered)`, wenn die E-Mail vergeben ist."""
        ...
