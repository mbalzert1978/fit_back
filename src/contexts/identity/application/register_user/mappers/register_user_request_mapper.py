"""Request-Mapper: public DTO -> internes Command. Eine Richtung, kein Rueckweg."""

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import (
    DisplayName,
    Email,
    IdnEncoder,
    Password,
    UserTimeZone,
    hydrate_locale,
)

__all__ = ["to_command"]


def to_command(request: RegisterUserRequest, idn: IdnEncoder) -> RegisterUserCommand:
    """Baue das Command aus dem bereits validierten Request.

    Infallibel und damit `hydrate` statt `parse`: die Collect-all-Validierung
    ist in der Pipeline vorgelagert gelaufen, der Kern-Handler sieht nie einen
    ungueltigen Request. Ein Fehlschlag hier waere ein Programmierfehler, kein
    Fachfall - deshalb `AssertionError` aus `hydrate` und kein Fehlerkanal.
    """
    return RegisterUserCommand(
        email=Email.hydrate(request.email, idn),
        password=Password.hydrate(request.password),
        display_name=DisplayName.hydrate(request.display_name),
        locale=hydrate_locale(request.locale),
        time_zone=UserTimeZone.hydrate(request.time_zone_id),
    )
