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
from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import group_by_field

__all__ = ["to_response"]


def to_response(outcome: Result[Registration, RegisterUserError]) -> RegisterUserResponse:
    """Uebersetze den Ausgang der Pipeline in die public Antwort."""
    match outcome:
        case Ok(value=Registration(user=user, session=session)):
            return RegistrationAccepted(
                user_id=str(user.id),
                email=user.email.value,
                display_name=user.display_name.value,
                locale=locale_tag(user.locale),
                time_zone_id=user.time_zone.value,
                registered_at_unix=user.registered_at.unix_seconds,
                access_token=session.access_token,
                expires_in=session.expires_in,
                refresh_token=session.refresh_token,
                refresh_expires_in=session.refresh_expires_in,
            )
        case Err(error=error):
            match error:
                case RequestInvalid(errors=errors):
                    return RegistrationInvalid(group_by_field(errors))
                case EmailAlreadyRegistered(email=email):
                    return EmailAlreadyTaken(email.value)
                case _:
                    assert_never(error)
        case _:
            assert_never(outcome)
