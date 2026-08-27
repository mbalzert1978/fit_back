"""Handler des Use Case RegisterUser - reiner Orchestrator."""

from typing import final

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.domain import (
    SessionIssuer,
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

    Kennt weder Request- noch Response-DTO - beides lebt in den Mappern. Faengt
    nichts ab und entscheidet nichts fachlich: welche Felder gueltig sind, weiss
    `UserFactory`, ob die E-Mail frei ist, weiss der Bestand, und wie eine
    Sitzung entsteht, weiss der Aussteller.

    Der **ganze** Ablauf steht hier, auch die Ausstellung der Sitzung. Sie war
    frueher ein eigener Schritt um den Handler herum; damit orchestrierten zwei
    Stellen (docs/decisions/2026-08-27-1630-die-sitzung-entsteht-im-handler.md).
    """

    def __init__(
        self,
        users: UserFactory,
        registry: UserRegistry,
        sessions: SessionIssuer,
        events: EventPublisher,
    ) -> None:
        """Nimm Fabrik, Bestand, Aussteller und Ereignis-Naht per Dependency Injection entgegen."""
        self._users = users
        self._registry = registry
        self._sessions = sessions
        self._events = events

    def __call__(
        self, command: RegisterUserCommand
    ) -> AsyncResult[Registration, RegisterUserFailure]:
        """Baue den Kandidaten, reiche ihn dem Bestand, melde ihn und stelle die Sitzung aus.

        `inspect_async` statt eines Match fuer die Meldung: gemeldet wird nur der
        aufgenommene User, und die Meldung aendert am Ergebnis nichts.
        `map_async` fuer die Sitzung: sie **aendert** das Ergebnis, kann aber
        nicht erwartet fehlschlagen - der Fehlerkanal bleibt unberuehrt, und eine
        abgelehnte Registrierung bekommt keinen Token.
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
            .inspect_async(self._announce)
            .map_async(self._with_session)
        )

    async def _announce(self, user: User) -> None:
        """Melde die abgeschlossene Registrierung nach aussen."""
        await self._events.publish(user_registered(user))

    async def _with_session(self, user: User) -> Registration:
        """Stelle die Sitzung aus und binde sie an den aufgenommenen User."""
        return Registration(user, await self._sessions.issue(user))
