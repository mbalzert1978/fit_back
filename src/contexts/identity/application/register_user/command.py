"""Internes Command des Use Case RegisterUser - die Rohwerte des Vertrags, ohne DTO."""

from dataclasses import dataclass, field
from typing import final

__all__ = ["RegisterUserCommand"]


@final
@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    """Was der Handler braucht - kein DTO mehr, und noch kein Value Object.

    Primitive und keine fertigen Value Objects: die VOs entstehen erst in
    `User.create`, weil dort die Invarianten der Wurzel hingehoeren. Traege das
    Command sie schon, entstuenden sie eine Schicht ausserhalb der Domaene - und
    der Use Case entschiede, welche Regeln sie gesehen haben.

    Die Konstruktion ist infallibel: geprueft wird eine Ebene hoeher
    (Collect-all fuer die 422) und danach noch einmal in der Wurzel selbst. Das
    Command traegt nur weiter.
    """

    email: str
    password: str = field(repr=False)
    display_name: str
    locale: str
    time_zone: str
