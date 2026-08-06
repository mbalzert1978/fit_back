"""Public Response-Union des Use Case RegisterUser.

Geschlossene Tagged Union statt "Ergebnis plus Fehlerliste": jeder Ausgang traegt
genau die Felder, die er hat. Der HTTP-Router (Stufe 3) matcht darauf und waehlt
Statuscode und ProblemDetails-Typ - er trifft dabei keine Fachentscheidung mehr.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

__all__ = [
    "EmailAlreadyTaken",
    "RegisterUserResponse",
    "RegistrationAccepted",
    "RegistrationInvalid",
]


@final
@dataclass(frozen=True, slots=True)
class RegistrationAccepted:
    """Das Konto wurde angelegt (HTTP 201)."""

    user_id: str
    email: str
    display_name: str
    locale: str
    time_zone_id: str
    registered_at_unix: int
    """Unix-Sekunden. Die ISO-8601-Formatierung fuer den Transport macht die HTTP-Schicht."""


@final
@dataclass(frozen=True, slots=True)
class EmailAlreadyTaken:
    """Die E-Mail gehoert bereits einem Konto (HTTP 409, email-already-registered)."""

    email: str


@final
@dataclass(frozen=True, slots=True)
class RegistrationInvalid:
    """Die Eingabe ist formal ungueltig (HTTP 400, gefuelltes `errors`-Objekt)."""

    errors: Mapping[str, tuple[str, ...]]


type RegisterUserResponse = RegistrationAccepted | EmailAlreadyTaken | RegistrationInvalid
