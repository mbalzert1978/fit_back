"""Response-Mapper: Ergebnis -> public Response-Union. Eine Richtung, kein Hinweg."""

from collections.abc import Iterable

from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.domain import DomainError, EmailAlreadyRegistered, User, locale_tag
from src.shared_kernel import Err, Ok, Result
from src.shared_kernel.validation import FieldError, group_by_field

__all__ = ["to_invalid_response", "to_response"]


def to_response(outcome: Result[User, DomainError]) -> RegisterUserResponse:
    """Uebersetze den Domaenen-Ausgang in die public Antwort.

    Vollstaendiges Matching ohne Auffangzweig: waechst `DomainError` um einen
    Fall, faellt genau hier auf, dass die Antwort dafuer noch fehlt.
    """
    match outcome:
        case Ok(value=user):
            return RegistrationAccepted(
                user_id=str(user.id),
                email=user.email.value,
                display_name=user.display_name.value,
                locale=locale_tag(user.locale),
                time_zone_id=user.time_zone.value,
                registered_at=user.registered_at,
            )
        case Err(error=EmailAlreadyRegistered(email=email)):
            return EmailAlreadyTaken(email.value)


def to_invalid_response(errors: Iterable[FieldError]) -> RegisterUserResponse:
    """Uebersetze gesammelte Feldfehler in die public Antwort."""
    return RegistrationInvalid(group_by_field(errors))
