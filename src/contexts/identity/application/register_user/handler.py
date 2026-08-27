"""Handler des Use Case RegisterUser - reiner Orchestrator."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RegisterUserTokenOptions,
)
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
        tokens: RegisterUserTokenOptions,
    ) -> None:
        """Nimm Fabrik, Bestand, Aussteller, Ereignis-Naht und Token-Konfiguration entgegen.

        `tokens` ist Konfiguration und kein Mitspieler: der Handler ruft darauf
        nichts auf, er liest zwei Zahlen und reicht sie als Primitive weiter.
        """
        self._users = users
        self._registry = registry
        self._sessions = sessions
        self._events = events
        self._tokens = tokens

    def __call__(
        self, command: RegisterUserCommand
    ) -> AsyncResult[Registration, RegisterUserFailure]:
        """Baue den Kandidaten, reiche ihn dem Bestand, stelle die Sitzung aus und melde ihn.

        Die Meldung steht **zuletzt**: sie behauptet, dass ein Konto samt seinem
        Refresh-Token entstanden ist. Vor der Ablage des Token waere das eine
        Zusage auf einen Zustand, den ein Fehlschlag danach noch zuruecknimmt.

        `inspect_async` statt eines Match fuer die Meldung: gemeldet wird nur die
        abgeschlossene Registrierung, und die Meldung aendert am Ergebnis nichts.
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
            self._tokens.access_token_seconds,
            self._tokens.refresh_token_seconds,
        )
        return Registration(user, credentials)
