"""Public Request-DTO des Use Case RegisterUser - ausschliesslich Primitive."""

from dataclasses import dataclass, field
from typing import final

__all__ = ["RegisterUserRequest"]


@final
@dataclass(frozen=True, slots=True)
class RegisterUserRequest:
    """Rohe, noch ungeprueft Registrierungsdaten von der Aussengrenze.

    Entspricht dem Body von `POST /api/v1/identity/register` (BACKEND.md
    Abschnitt 1); die Feldnamen sind hier snake_case, die Uebersetzung nach
    camelCase ist Sache der HTTP-Schicht (Stufe 3).
    """

    email: str
    password: str = field(repr=False)
    display_name: str
    locale: str
    time_zone_id: str
