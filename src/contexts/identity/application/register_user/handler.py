"""Handler des Use Case RegisterUser - reiner Orchestrator."""

from typing import final

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.domain import (
    SessionIssuer,
    TokenLifetime,
    User,
    UserFactory,
    UserRegistry,
    UserRegistryError,
    UserRejected,
    user_registered,
)
from src.contexts.shared_kernel import AsyncResult
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

    Kennt weder Request- noch Response-DTO - beides lebt in den Mappern. Der
    **ganze** Ablauf steht hier, auch die Ausstellung der Sitzung
    (docs/decisions/2026-08-27-1630-die-sitzung-entsteht-im-handler.md).
    """

    def __init__(  # noqa: PLR0913, PLR0917 -- je Mitspieler ein Parameter, plus die zwei Dauern
        self,
        users: UserFactory,
        registry: UserRegistry,
        sessions: SessionIssuer,
        events: EventPublisher,
        access_lifetime: TokenLifetime,
        refresh_lifetime: TokenLifetime,
    ) -> None:
        """Nimm Fabrik, Bestand, Aussteller, Ereignis-Naht und die beiden Geltungsdauern entgegen.

        Die Dauern kommen bereits als Domaenentyp herein - umgewandelt wird in
        der Fabrik (`pipeline.py`), an der aeusseren Naht.
        """
        self._users = users
        self._registry = registry
        self._sessions = sessions
        self._events = events
        self._access_lifetime = access_lifetime
        self._refresh_lifetime = refresh_lifetime

    def __call__(
        self, command: RegisterUserCommand
    ) -> AsyncResult[Registration, RegisterUserFailure]:
        """Baue den Kandidaten, reiche ihn dem Bestand, stelle die Sitzung aus und melde ihn.

        Die Meldung steht **zuletzt**
        (docs/decisions/2026-08-27-1945-gemeldet-wird-erst-am-ende.md).
        """
        return (
            self._users.create(
                email=command.email,
                password=command.password,
                display_name=command.display_name,
                locale=command.locale,
                time_zone=command.time_zone,
            )
            .bind_async(self._registry.add)
            .map_async(self._with_credentials)
            .inspect_async(self._announce)
        )

    async def _announce(self, registration: Registration) -> None:
        """Melde die abgeschlossene Registrierung nach aussen."""
        await self._events.publish(user_registered(registration.user))

    async def _with_credentials(self, user: User) -> Registration:
        """Stelle die Zugangsdaten aus und binde sie an den aufgenommenen User."""
        credentials = await self._sessions.issue(
            user,
            self._access_lifetime,
            self._refresh_lifetime,
        )
        return Registration(user, credentials)
