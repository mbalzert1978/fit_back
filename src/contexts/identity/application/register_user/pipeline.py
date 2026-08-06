"""Die Pipeline des Use Case RegisterUser - Validierung, Mapper, Handler, Mapper.

Das ist die eine Stelle, an der der Slice zusammengesteckt wird
(.rules/python/python-factories.md). Produktion und Test-API benutzen **dieselbe**
Fabrik; getauscht wird ausschliesslich, was hinter der public Naht steckt.
"""

from typing import final

from src.contexts.identity.application.register_user.adapters import (
    PasswordHasherAdapter,
    UserRegistryAdapter,
)
from src.contexts.identity.application.register_user.gateway import (
    RegisterUserPasswordHasher,
    RegisterUserUserStore,
)
from src.contexts.identity.application.register_user.handler import RegisterUserHandler
from src.contexts.identity.application.register_user.register_user_request_mapper import to_command
from src.contexts.identity.application.register_user.register_user_response_mapper import (
    to_invalid_response,
    to_response,
)
from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.application.register_user.response import RegisterUserResponse
from src.contexts.identity.application.register_user.validators import register_user_rules
from src.shared_kernel import TimeProvider
from src.shared_kernel.validation import Rule

__all__ = ["RegisterUserPipeline", "build_register_user_pipeline"]


@final
class RegisterUserPipeline:
    """Fuehrt den Use Case vom public Request zur public Response."""

    def __init__(
        self,
        validate: Rule[RegisterUserRequest],
        handler: RegisterUserHandler,
    ) -> None:
        """Nimm Regelwerk und Handler entgegen."""
        self._validate = validate
        self._handler = handler

    async def run(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """Validiere, mappe hinein, orchestriere, mappe heraus."""
        if errors := self._validate(request):
            return to_invalid_response(errors)
        return to_response(await self._handler(to_command(request)))


def build_register_user_pipeline(
    store: RegisterUserUserStore,
    hasher: RegisterUserPasswordHasher,
    clock: TimeProvider,
) -> RegisterUserPipeline:
    """Verdrahte den Slice gegen eine beliebige Implementierung der public Naht."""
    return RegisterUserPipeline(
        validate=register_user_rules,
        handler=RegisterUserHandler(
            registry=UserRegistryAdapter(store),
            hasher=PasswordHasherAdapter(hasher),
            clock=clock,
        ),
    )
