"""Domain-Port UserRegistry - das Verzeichnis, das die E-Mail-Eindeutigkeit haelt."""

from typing import Protocol

from src.contexts.identity.domain.entities.user import User
from src.contexts.identity.domain.errors import DomainError
from src.contexts.identity.domain.value_objects.email import Email
from src.shared_kernel import Result

__all__ = ["UserRegistry"]


class UserRegistry(Protocol):
    """Von der Domaene vorgegebener Port - spricht ausschliesslich Value Objects.

    Ehrlich fehlbar: beide Operationen koennen an genau derselben Invariante
    scheitern (die E-Mail ist schon vergeben) und melden das als
    `Result[..., DomainError]`, nicht als Exception.
    """

    async def claim_email(self, email: Email) -> Result[Email, DomainError]:
        """Beanspruche die E-Mail; `Err`, wenn sie bereits einem Konto gehoert."""
        ...

    async def add(self, user: User) -> Result[User, DomainError]:
        """Nimm den User auf; `Err`, wenn die E-Mail zwischenzeitlich vergeben wurde."""
        ...
