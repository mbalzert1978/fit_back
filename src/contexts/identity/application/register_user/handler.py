"""Handler des Use Case RegisterUser - reiner Orchestrator."""

from typing import final

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.domain import (
    DomainError,
    PasswordHasher,
    User,
    UserId,
    UserRegistry,
    register,
)
from src.shared_kernel import Result, TimeProvider

__all__ = ["RegisterUserHandler"]


@final
class RegisterUserHandler:
    """Baut die Aggregatwurzel und uebergibt sie dem Nutzerbestand.

    Kennt weder Request- noch Response-DTO - beides lebt in den Mappern. Faengt
    nichts ab, entscheidet nichts fachlich und liefert das Domaenen-`Result`
    unveraendert zurueck: es ist bereits das vollstaendige Ergebnis, ein eigener
    Outcome-Typ waere nur Zeremonie.
    """

    def __init__(
        self,
        registry: UserRegistry,
        hasher: PasswordHasher,
        clock: TimeProvider,
    ) -> None:
        """Nimm die Ports und die Zeitquelle per Dependency Injection entgegen."""
        self._registry = registry
        self._hasher = hasher
        self._clock = clock

    async def __call__(self, command: RegisterUserCommand) -> Result[User, DomainError]:
        """Registriere den Kandidaten."""
        candidate = register(
            user_id=UserId.generate(),
            email=command.email,
            password_hash=await self._hasher.hash(command.password),
            display_name=command.display_name,
            time_zone=command.time_zone,
            locale=command.locale,
            registered_at=self._clock.now(),
        )
        return await self._registry.add(candidate)
