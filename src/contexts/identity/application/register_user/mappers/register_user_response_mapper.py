"""Response-Mapper: Ergebnis der Pipeline -> public Response-Union."""

from functools import partial
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
from src.contexts.identity.domain import EmailAlreadyRegistered, User, locale_tag
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
    """Der erfolgreiche Ausgang - eine Registrierung wird zur Bestaetigung.

    Die Zugangsdaten werden **gefragt**, nicht ausgelesen: der Mapper sagt, was
    er bauen will, und bekommt die vier Werte gereicht. Vorher stand hier viermal
    eine Kette durch zwei fremde Objekte
    (docs/decisions/2026-08-28-1120-die-zugangsdaten-geben-heraus-was-sie-wissen.md).
    """
    return registration.credentials.fold(partial(_with_user, registration.user))


def _with_user(
    user: User,
    access_token: str,
    expires_in: int,
    refresh_token: str,
    refresh_expires_in: int,
) -> RegisterUserResponse:
    """Setze die Bestaetigung aus Stammdaten und den beiden Ausgaben zusammen."""
    return RegistrationAccepted(
        user_id=str(user.id),
        email=user.email.value,
        display_name=user.display_name.value,
        locale=locale_tag(user.locale),
        time_zone_id=user.time_zone.value,
        registered_at_unix=user.registered_at.unix_seconds,
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=refresh_token,
        refresh_expires_in=refresh_expires_in,
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
