"""Die Pipeline des Use Case RegisterUser - eine Kette von Behaviors um den Handler.

Das ist die eine Stelle, an der der Slice zusammengesteckt wird
(.rules/python/python-factories.md). Produktion und Test-API benutzen **dieselbe**
Fabrik; getauscht wird ausschliesslich, was hinter der public Naht steckt.

Die Kette (`shared_kernel/pipeline.py`) ersetzt seit Stufe 4 von Ticket 0011 den
frueheren Wrapper mit `if`: dort standen zwei Fehlerkanaele und zwei Folds in
dieselbe Response-Union, verbunden durch eine imperative Verzweigung. Jetzt hebt
das erste Behavior die Feldfehler in **denselben** Fehlerkanal, in dem auch der
Domaenenfehler ankommt, und am Ende steht genau ein Fold.

Wo Querschnittliches hingehoert, ist damit beantwortet: als weiteres Behavior in
diese Kette - Transaktionsklammer, Idempotenz, Messung, Logging -, nicht als
weiterer Absatz in `run`.
"""

from typing import assert_never, final

from src.contexts.identity.application.register_user.abstractions import (
    IdnLabels,
    RegisterUserEventLog,
    RegisterUserPasswordHasher,
    RegisterUserSessionTokens,
    RegisterUserUserStore,
)
from src.contexts.identity.application.register_user.adapters import (
    EventPublisherAdapter,
    IdnEncoderAdapter,
    PasswordHasherAdapter,
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
from src.contexts.identity.application.register_user.mappers import to_command, to_response
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.application.register_user.response import RegisterUserResponse
from src.contexts.identity.application.register_user.session_step import issuing_session
from src.contexts.identity.application.register_user.validators import (
    build_register_user_rules,
    to_field_errors,
)
from src.contexts.identity.domain import (
    DisplayNameRejected,
    EmailAlreadyRegistered,
    EmailRejected,
    LocaleRejected,
    PasswordRejected,
    TimeZoneRejected,
    User,
)
from src.contexts.shared_kernel import AsyncResult, TimeProvider
from src.contexts.shared_kernel.behaviors import validating
from src.contexts.shared_kernel.pipeline import Handler, build_pipeline
from src.contexts.shared_kernel.validation import as_async

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
    clock: TimeProvider,
) -> RegisterUserPipeline:
    """Verdrahte den Slice gegen eine beliebige Implementierung der public Naht."""
    idn = IdnEncoderAdapter(labels)
    handler = RegisterUserHandler(
        registry=UserRegistryAdapter(store),
        hasher=PasswordHasherAdapter(hasher),
        events=EventPublisherAdapter(events),
        clock=clock,
        idn=idn,
    )
    return RegisterUserPipeline(
        build_pipeline(
            issuing_session(_dispatch(handler), sessions),
            validating(as_async(build_register_user_rules(idn)), request_invalid),
        )
    )


def _dispatch(
    handler: RegisterUserHandler,
) -> Handler[RegisterUserRequest, User, RegisterUserError]:
    """Baue den innersten Schritt: Request-Mapper, Handler und ein Fehler-Kanal.

    `to_command` steht hier und nicht im Handler, weil der Kern-Handler das
    Request-DTO nicht kennen darf (.rules/python/python-feature-slices.md). Er
    parst nichts mehr - das tut die Wurzel selbst -, und deshalb braucht er den
    IDN-Port hier auch nicht mehr.

    Der `map_err` fuehrt die beiden Haelften des Handler-Fehlers in den **einen**
    Kanal der Pipeline zusammen: eine von der Wurzel abgelehnte Eingabe ist
    derselbe Fall wie eine vom Regelwerk abgelehnte, und am Ende steht genau ein
    Fold.

    Die Sitzung kommt eine Schicht weiter aussen dazu
    ([`session_step.py`](./session_step.py)) - sie ist Fachablauf und steht
    deshalb nicht in diesem Verdrahtungs-Modul.
    """

    def run(request: RegisterUserRequest) -> AsyncResult[User, RegisterUserError]:
        return handler(to_command(request)).map_err(_as_use_case_error)

    return run


def _as_use_case_error(rejected: RegisterUserFailure) -> RegisterUserError:
    """Hebe den Fehler des Handlers in den Fehlerkanal des Use Case."""
    match rejected:
        case EmailAlreadyRegistered():
            return rejected
        case (
            EmailRejected()
            | PasswordRejected()
            | DisplayNameRejected()
            | LocaleRejected()
            | TimeZoneRejected()
        ):
            return request_invalid(to_field_errors(rejected))
        case _:
            assert_never(rejected)
