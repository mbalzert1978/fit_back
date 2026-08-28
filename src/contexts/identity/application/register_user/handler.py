"""Handler des Use Case RegisterUser - reiner Orchestrator."""

from typing import final

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.domain import (
    AccessTokens,
    IssuedCredentials,
    RefreshToken,
    RefreshTokens,
    TokenLifetimes,
    TokenSecrets,
    User,
    UserFactory,
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

    Kennt weder Request- noch Response-DTO - beides lebt in den Mappern. Der
    **ganze** Ablauf steht hier, auch die Ausstellung der Sitzung
    (docs/decisions/2026-08-27-1630-die-sitzung-entsteht-im-handler.md,
    docs/decisions/2026-08-28-1450-der-handler-orchestriert-die-ausstellung.md).
    """

    def __init__(  # noqa: PLR0913, PLR0917 -- je Mitspieler ein Parameter, nicht mehr
        self,
        users: UserFactory,
        registry: UserRegistry,
        secrets: TokenSecrets,
        refresh_tokens: RefreshTokens,
        access_tokens: AccessTokens,
        events: EventPublisher,
        clock: TimeProvider,
        lifetimes: TokenLifetimes,
    ) -> None:
        """Nimm Fabrik, Bestand, die drei Token-Mitspieler, Ereignis-Naht, Uhr und Dauern entgegen.

        Die Dauern kommen bereits als Domaenentyp herein - umgewandelt wird in
        der Fabrik (`pipeline.py`), an der aeusseren Naht.
        """
        self._users = users
        self._registry = registry
        self._secrets = secrets
        self._refresh_tokens = refresh_tokens
        self._access_tokens = access_tokens
        self._events = events
        self._clock = clock
        self._lifetimes = lifetimes

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
        """Stelle beide Token aus, lege den Refresh-Token ab und paare die Ausgaben.

        Vom `User` wird ausschliesslich die Identitaet gebraucht; ausgestellt
        wird von den beiden Mitspielern selbst. `issued_at` ist **eine**
        Ablesung fuer beide Token.
        """
        issued_at = self._clock.now()
        issuance = RefreshToken.issue(
            user_id=user.id,
            secrets=self._secrets,
            issued_at=issued_at,
            lifetime=self._lifetimes.refresh,
        )
        await self._refresh_tokens.store(issuance.refresh_token)
        return Registration(
            user,
            IssuedCredentials.hydrate(
                self._access_tokens.sign(user.id, issued_at, self._lifetimes.access),
                issuance.grant,
            ),
        )
