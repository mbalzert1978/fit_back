"""Handler des Use Case RegisterUser - reiner Orchestrator."""

from typing import final

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.domain import (
    IdnEncoder,
    PasswordHasher,
    User,
    UserRegistry,
    UserRegistryError,
    UserRejected,
    user_registered,
)
from src.contexts.shared_kernel import AsyncResult, TimeProvider
from src.contexts.shared_kernel.events import EventPublisher

__all__ = ["RegisterUserFailure", "RegisterUserHandler"]


type RegisterUserFailure = UserRejected | UserRegistryError
"""Die beiden Stellen, an denen dieser Use Case erwartet scheitern kann.

Ausgeschrieben und nicht ueber einen Sammeltyp gebildet: jede Haelfte traegt
weiterhin ihre eigene, schmale Union.
"""


@final
class RegisterUserHandler:
    """Laesst die Wurzel sich selbst bauen und uebergibt sie dem Nutzerbestand.

    Kennt weder Request- noch Response-DTO - beides lebt in den Mappern. Faengt
    nichts ab und entscheidet nichts fachlich: welche Felder gueltig sind, weiss
    `User.create`, und ob die E-Mail frei ist, weiss der Bestand.

    Die Ports gehen durch ihn hindurch zur Wurzel, statt dass er selbst mit ihnen
    arbeitet. Er haelt sie nur, damit die Wurzel sie nicht suchen muss.
    """

    def __init__(
        self,
        registry: UserRegistry,
        hasher: PasswordHasher,
        events: EventPublisher,
        clock: TimeProvider,
        idn: IdnEncoder,
    ) -> None:
        """Nimm die Ports und die Zeitquelle per Dependency Injection entgegen."""
        self._registry = registry
        self._hasher = hasher
        self._events = events
        self._clock = clock
        self._idn = idn

    def __call__(self, command: RegisterUserCommand) -> AsyncResult[User, RegisterUserFailure]:
        """Baue den Kandidaten, reiche ihn dem Bestand und melde die Aufnahme.

        `inspect_async` statt eines Match am Ende: gemeldet wird nur der
        aufgenommene User, und die Meldung aendert am Ergebnis nichts.
        """
        return (
            User.create(
                email=command.email,
                password=command.password,
                display_name=command.display_name,
                locale=command.locale,
                time_zone=command.time_zone,
                idn=self._idn,
                hasher=self._hasher,
                clock=self._clock,
            )
            .bind_async(self._registry.add)
            .inspect_async(self._announce)
        )

    async def _announce(self, user: User) -> None:
        """Melde die abgeschlossene Registrierung nach aussen."""
        await self._events.publish(user_registered(user))
