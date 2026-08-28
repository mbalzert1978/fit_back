"""Response-Mapper: Ergebnis der Pipeline -> public Response-Union."""

from typing import assert_never

from src.contexts.identity.application.register_user.errors import (
    RegisterUserError,
    RequestInvalid,
)
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import EmailAlreadyRegistered, locale_tag
from src.contexts.shared_kernel import Result
from src.contexts.shared_kernel.validation import group_by_field

__all__ = ["to_response"]


def to_response(outcome: Result[Registration, RegisterUserError]) -> RegisterUserResponse:
    """Uebersetze den Ausgang der Pipeline in die public Antwort.

    Ein Fold, kein Zweig - `Result.fold` ist der Eliminator, der den
    `Ok`/`Err`-Split ein einziges Mal in `result.py` aufloest statt hier. Die
    beiden Arme unten sind seine Faelle, nicht ein zweiter Fold: es bleibt bei
    **einem** Aufruf, der die eine Response-Union erzeugt
    (`docs/decisions/2026-08-26-1130-result-fold-als-eliminator.md`).
    """
    return outcome.fold(_accepted, _rejected)


def _accepted(registration: Registration) -> RegisterUserResponse:
    """Der erfolgreiche Ausgang - eine Registrierung wird zur Bestaetigung."""
    user, credentials = registration.user, registration.credentials
    return RegistrationAccepted(
        user_id=str(user.id),
        email=user.email.value,
        display_name=user.display_name.value,
        locale=locale_tag(user.locale),
        time_zone_id=user.time_zone.value,
        registered_at_unix=user.registered_at.unix_seconds,
        access_token=credentials.access_token,
        expires_in=credentials.access_lifetime.seconds,
        refresh_token=credentials.refresh_token,
        refresh_expires_in=credentials.refresh_lifetime.seconds,
    )


def _rejected(error: RegisterUserError) -> RegisterUserResponse:
    """Der Fehlschlag - flach ueber die Fehler-Union, damit `ty` die Vollzaehligkeit ausrechnet."""
    match error:
        case RequestInvalid(errors=errors):
            return RegistrationInvalid(group_by_field(errors))
        case EmailAlreadyRegistered(email=email):
            return EmailAlreadyTaken(email.value)
        case _:
            assert_never(error)
