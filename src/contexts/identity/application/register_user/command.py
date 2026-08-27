"""Internes Command des Use Case RegisterUser - die Rohwerte des Vertrags, ohne DTO."""

from dataclasses import dataclass, field
from typing import final

__all__ = ["RegisterUserCommand"]


@final
@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    """Was der Handler braucht - kein DTO mehr, und noch kein Value Object.

    Die Konstruktion prueft nichts. Geprueft wird ausschliesslich in
    `User.create` (docs/decisions/2026-08-26-2330-die-wurzel-sammelt-ihre-befunde-selbst.md).
    """

    email: str
    password: str = field(repr=False)
    display_name: str
    locale: str
    time_zone: str
