"""Public Response-Union des Use Case RegisterUser.

Geschlossene Tagged Union statt "Ergebnis plus Fehlerliste": jeder Ausgang traegt
genau die Felder, die er hat. Der HTTP-Router (Stufe 3) matcht darauf und waehlt
Statuscode und ProblemDetails-Typ - er trifft dabei keine Fachentscheidung mehr.

Die `errors`-Struktur traegt Code + Parameter statt fertige Texte: der HTTP-Rand
waehlt `Accept-Language` und rendert daraus.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from src.contexts.shared_kernel.validation import FieldErrorDetail

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
    """Die Eingabe ist formal ungueltig (HTTP 400, gefuelltes `errors`-Objekt).

    `errors` traegt eine Abbildung von Feldnamen zu Tupeln von (error_code, parameters).
    Der HTTP-Rand waehlt nach `Accept-Language` die Sprache und rendert die Codes.
    """

    errors: Mapping[str, tuple[FieldErrorDetail, ...]]


type RegisterUserResponse = RegistrationAccepted | EmailAlreadyTaken | RegistrationInvalid
