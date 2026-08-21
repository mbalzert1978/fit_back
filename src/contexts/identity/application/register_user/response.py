"""Public Response-Union des Use Case RegisterUser.

Geschlossene Tagged Union statt "Ergebnis plus Fehlerliste": jeder Ausgang traegt
genau die Felder, die er hat. Der HTTP-Router (Stufe 3) matcht darauf und waehlt
Statuscode und ProblemDetails-Typ - er trifft dabei keine Fachentscheidung mehr.

Die `errors`-Struktur traegt Code + Parameter statt fertige Texte: der HTTP-Rand
waehlt `Accept-Language` und rendert daraus.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar, final

from src.contexts.shared_kernel.validation import FieldErrorDetail

__all__ = [
    "EmailAlreadyTaken",
    "RegisterUserFailure",
    "RegisterUserResponse",
    "RegistrationAccepted",
    "RegistrationInvalid",
]


@final
@dataclass(frozen=True, slots=True)
class RegistrationAccepted:
    """Das Konto wurde angelegt (HTTP 201), samt der Sitzung dazu.

    Die vier Sitzungsfelder liegen flach und nicht als verschachteltes Objekt:
    der Vertrag des Frontends gibt sie unter `data.session` heraus, aber diese
    Gliederung ist Sache des HTTP-Randes. Wie die beiden Token heissen, mit denen
    der Aufrufer weiterarbeitet, ist eine Auskunft des Use Case.
    """

    user_id: str
    email: str
    display_name: str
    locale: str
    time_zone_id: str
    registered_at_unix: int
    """Unix-Sekunden. Die ISO-8601-Formatierung fuer den Transport macht die HTTP-Schicht."""

    access_token: str = field(repr=False)
    expires_in: int
    refresh_token: str = field(repr=False)
    refresh_expires_in: int


@final
@dataclass(frozen=True, slots=True)
class EmailAlreadyTaken:
    """Die E-Mail gehoert bereits einem Konto (HTTP 409, email-already-registered)."""

    code: ClassVar[str] = "email-already-registered"
    email: str


@final
@dataclass(frozen=True, slots=True)
class RegistrationInvalid:
    """Die Eingabe ist formal ungueltig (HTTP 422, gefuelltes `errors`-Objekt).

    `errors` traegt eine Abbildung von Feldnamen zu Tupeln von (error_code, parameters).
    Der HTTP-Rand waehlt nach `Accept-Language` die Sprache und rendert die Codes.
    Der top-level code ist 'validation-failed', die Feldfehlercodes sind in den `errors` Eintraegen.
    """

    code: ClassVar[str] = "validation-failed"
    errors: Mapping[str, tuple[FieldErrorDetail, ...]]


type RegisterUserFailure = EmailAlreadyTaken | RegistrationInvalid
"""Die Fehlerhaelfte der Antwort - jeder Fall traegt seinen Code.

Eigener Name, damit der Zusammenbau sie der Drift-Pruefung uebergeben kann, ohne den
Erfolgsfall mitzuschleppen: `RegistrationAccepted` hat zu Recht keinen Fehlercode, und
eine Aufzaehlung, die ihn ueberspringen muesste, koennte einen vergessenen Code nicht
mehr von einem Erfolg unterscheiden.
"""

type RegisterUserResponse = RegistrationAccepted | RegisterUserFailure
