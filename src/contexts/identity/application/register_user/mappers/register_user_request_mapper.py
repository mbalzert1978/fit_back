"""Request-Mapper: public DTO -> internes Command. Eine Richtung, kein Rueckweg."""

from src.contexts.identity.application.register_user.command import RegisterUserCommand
from src.contexts.identity.application.register_user.request import RegisterUserRequest

__all__ = ["to_command"]


def to_command(request: RegisterUserRequest) -> RegisterUserCommand:
    """Baue das Command aus dem Request - Feldnamen des Vertrags auf interne.

    Kein Parsen und deshalb auch kein IDN-Port mehr: die Value Objects entstehen
    in `User.create`, weil die Wurzel ihre Invarianten selbst haelt. Hier bleibt
    genau das, wofuer ein Mapper da ist - `timeZoneId` heisst innen `time_zone`,
    und das public DTO endet an dieser Zeile.
    """
    return RegisterUserCommand(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        locale=request.locale,
        time_zone=request.time_zone_id,
    )
