"""Die Pipeline des Use Case RegisterUser - eine Kette von Behaviors um den Handler.

Das ist die eine Stelle, an der der Slice zusammengesteckt wird
(.rules/python/python-factories.md). Produktion und Test-API benutzen **dieselbe**
Fabrik; getauscht wird ausschliesslich, was hinter der public Naht steckt.

Warum eine Kette und kein Wrapper mit `if`:
docs/decisions/2026-08-17-0937-pipeline-als-behavior-kette-im-shared-kernel.md.

Ein Validierungs-Behavior steht **nicht** mehr davor - es pruefte dieselben
Felder wie `UserFactory.create`. `validating` bleibt als Baustein bestehen, fuer
Regeln, die keine Wurzel beantworten kann.

Wo Querschnittliches hingehoert, ist damit beantwortet: als weiteres Behavior in
diese Kette - Transaktionsklammer, Idempotenz, Messung, Logging -, nicht als
weiterer Absatz in `run`.
"""

from typing import assert_never, final

from src.contexts.identity.application.register_user.abstractions import (
    IdnLabels,
    RegisterUserAccessTokens,
    RegisterUserEventLog,
    RegisterUserPasswordHasher,
    RegisterUserSessionTokens,
    RegisterUserTokenOptions,
    RegisterUserUserStore,
)
from src.contexts.identity.application.register_user.adapters import (
    EventPublisherAdapter,
    IdnEncoderAdapter,
    PasswordHasherAdapter,
    SessionIssuerAdapter,
    UserRegistryAdapter,
)
from src.contexts.identity.application.register_user.errors import (
    RegisterUserError,
    request_invalid,
)
from src.contexts.identity.application.register_user.handler import (
    RegisterUserFailure,
    RegisterUserHandler,
)
from src.contexts.identity.application.register_user.mappers import (
    to_command,
    to_field_errors,
    to_response,
)
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.application.register_user.response import RegisterUserResponse
from src.contexts.identity.domain import (
    EmailAlreadyRegistered,
    UserFactory,
    UserRejected,
)
from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.shared_kernel import AsyncResult, TimeProvider
from src.contexts.shared_kernel.pipeline import Handler, build_pipeline

__all__ = ["RegisterUserPipeline", "build_register_user_pipeline"]

type RegisterUserStep = Handler[RegisterUserRequest, Registration, RegisterUserError]
"""Die Signatur, die Handler und Behaviors dieses Use Case gemeinsam tragen."""


@final
class RegisterUserPipeline:
    """Fuehrt den Use Case vom public Request zur public Response."""

    def __init__(self, chain: RegisterUserStep) -> None:
        """Nimm die fertig verkettete Pipeline entgegen."""
        self._chain = chain

    async def run(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """Lass die Kette laufen und falte ihr Ergebnis in die public Antwort."""
        return to_response(await self._chain(request))


def build_register_user_pipeline(  # noqa: PLR0913, PLR0917 -- Fabrik: je Naht ein Parameter, nicht mehr
    store: RegisterUserUserStore,
    hasher: RegisterUserPasswordHasher,
    labels: IdnLabels,
    events: RegisterUserEventLog,
    sessions: RegisterUserSessionTokens,
    access_tokens: RegisterUserAccessTokens,
    clock: TimeProvider,
    tokens: RegisterUserTokenOptions,
) -> RegisterUserPipeline:
    """Verdrahte den Slice gegen eine beliebige Implementierung der public Naht."""
    handler = RegisterUserHandler(
        users=UserFactory(
            idn=IdnEncoderAdapter(labels),
            hasher=PasswordHasherAdapter(hasher),
            clock=clock,
        ),
        registry=UserRegistryAdapter(store),
        sessions=SessionIssuerAdapter(sessions, access_tokens),
        events=EventPublisherAdapter(events),
        access_lifetime=TokenLifetime.hydrate(tokens.access_token_seconds),
        refresh_lifetime=TokenLifetime.hydrate(tokens.refresh_token_seconds),
    )
    return RegisterUserPipeline(build_pipeline(_dispatch(handler)))


def _dispatch(
    handler: RegisterUserHandler,
) -> Handler[RegisterUserRequest, Registration, RegisterUserError]:
    """Baue den innersten Schritt: Request-Mapper, Handler und ein Fehler-Kanal.

    `to_command` steht hier und nicht im Handler, weil der Kern-Handler das
    Request-DTO nicht kennen darf (.rules/python/python-feature-slices.md).

    Der Fachablauf steht vollstaendig im Handler - auch die Ausstellung der
    Sitzung. Dieses Modul verdrahtet nur.
    """

    def run(request: RegisterUserRequest) -> AsyncResult[Registration, RegisterUserError]:
        return handler(to_command(request)).map_err(_as_use_case_error)

    return run


def _as_use_case_error(rejected: RegisterUserFailure) -> RegisterUserError:
    """Hebe den Fehler des Handlers in den Fehlerkanal des Use Case."""
    match rejected:
        case EmailAlreadyRegistered():
            return rejected
        case UserRejected():
            return request_invalid(to_field_errors(rejected))
        case _:
            assert_never(rejected)
