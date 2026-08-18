"""Handler des Use Case RegisterUser - reiner Orchestrator."""

from typing import final

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.domain import (
    PasswordHasher,
    User,
    UserId,
    UserRegistry,
    UserRegistryError,
    register,
    user_registered,
)
from src.contexts.shared_kernel import Result, TimeProvider
from src.contexts.shared_kernel.events import EventPublisher

__all__ = ["RegisterUserHandler"]


@final
class RegisterUserHandler:
    """Baut die Aggregatwurzel und uebergibt sie dem Nutzerbestand.

    Kennt weder Request- noch Response-DTO - beides lebt in den Mappern. Faengt
    nichts ab, entscheidet nichts fachlich und liefert das Domaenen-`Result`
    unveraendert zurueck: es ist bereits das vollstaendige Ergebnis, ein eigener
    Outcome-Typ waere nur Zeremonie.

    Der Fehlertyp ist der des einen Ports, der hier fehlschlagen kann
    (`UserRegistryError`) - nicht der Sammeltyp des Contexts. Was der Handler
    weitergibt, ist damit genau das, was ankommen kann.
    """

    def __init__(
        self,
        registry: UserRegistry,
        hasher: PasswordHasher,
        events: EventPublisher,
        clock: TimeProvider,
    ) -> None:
        """Nimm die Ports und die Zeitquelle per Dependency Injection entgegen."""
        self._registry = registry
        self._hasher = hasher
        self._events = events
        self._clock = clock

    async def __call__(self, command: RegisterUserCommand) -> Result[User, UserRegistryError]:
        """Registriere den Kandidaten und melde die Registrierung."""
        candidate = register(
            user_id=UserId.generate(),
            email=command.email,
            password_hash=await self._hasher.hash(command.password),
            display_name=command.display_name,
            time_zone=command.time_zone,
            locale=command.locale,
            registered_at=self._clock.now(),
        )
        # `inspect_async` statt eines Match: gemeldet wird nur der aufgenommene
        # User - eine abgelehnte Registrierung ist nichts, worauf ein anderer
        # Context reagieren duerfte - und die Meldung selbst aendert am Ergebnis
        # des Use Case nichts.
        registered = await self._registry.add(candidate)
        return await registered.inspect_async(self._announce)

    async def _announce(self, user: User) -> None:
        """Melde die abgeschlossene Registrierung nach aussen."""
        await self._events.publish(user_registered(user))
