"""Die Faelle des `DomainError`, die den Aufbau einer E-Mail-Adresse betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
Der Grund fuer die Trennung ist ein Importzyklus - `errors.py` braucht das
`Email`-Value-Object fuer `EmailAlreadyRegistered`, und `email.py` braucht diese
Faelle. Da hier ausschliesslich Primitive als Nutzlast vorkommen, haengt dieses
Modul an nichts und kann von beiden Seiten importiert werden.

Genau dieselbe Aufteilung wie bei den Value Objects: physisch gegliedert,
im Namespace ueber `domain/__init__.py` flach.
"""

from dataclasses import dataclass
from typing import final

__all__ = [
    "EmailAddressLiteralInvalid",
    "EmailDomainHasEmptyLabel",
    "EmailDomainLabelHasEdgeHyphen",
    "EmailDomainLabelHasInvalidCharacters",
    "EmailDomainLabelTooLong",
    "EmailDomainMissing",
    "EmailDomainTooLong",
    "EmailError",
    "EmailHasWhitespace",
    "EmailLocalPartHasInvalidCharacters",
    "EmailLocalPartHasMisplacedDot",
    "EmailLocalPartMissing",
    "EmailLocalPartTooLong",
    "EmailNeedsExactlyOneAtSign",
    "UnencodableDomainLabel",
]


@final
@dataclass(frozen=True, slots=True)
class EmailHasWhitespace:
    """Die Adresse enthaelt Leerraum - bei einem Zeilenumbruch ein Injection-Versuch."""

    candidate: str


@final
@dataclass(frozen=True, slots=True)
class EmailNeedsExactlyOneAtSign:
    """Die Adresse hat kein oder mehr als ein `@`."""

    candidate: str
    at_sign_count: int


@final
@dataclass(frozen=True, slots=True)
class EmailLocalPartMissing:
    """Vor dem `@` steht nichts."""

    candidate: str


@final
@dataclass(frozen=True, slots=True)
class EmailDomainMissing:
    """Hinter dem `@` steht nichts."""

    candidate: str


@final
@dataclass(frozen=True, slots=True)
class EmailLocalPartTooLong:
    """Der Teil vor dem `@` ueberschreitet die zulaessige Laenge."""

    local_part: str
    maximum: int


@final
@dataclass(frozen=True, slots=True)
class EmailLocalPartHasInvalidCharacters:
    """Der Teil vor dem `@` enthaelt nicht erlaubte Zeichen."""

    local_part: str
    invalid_characters: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class EmailLocalPartHasMisplacedDot:
    """Der Teil vor dem `@` beginnt/endet mit einem Punkt oder hat zwei in Folge."""

    local_part: str


@final
@dataclass(frozen=True, slots=True)
class EmailDomainTooLong:
    """Die Domain ueberschreitet die zulaessige Gesamtlaenge."""

    domain: str
    maximum: int


@final
@dataclass(frozen=True, slots=True)
class EmailDomainHasEmptyLabel:
    """Die Domain enthaelt ein leeres Label - fuehrender, doppelter oder Schlusspunkt."""

    domain: str


@final
@dataclass(frozen=True, slots=True)
class EmailDomainLabelTooLong:
    """Ein Domain-Label ueberschreitet in seiner ASCII-Form die zulaessige Laenge."""

    label: str
    ascii_length: int
    maximum: int


@final
@dataclass(frozen=True, slots=True)
class EmailDomainLabelHasEdgeHyphen:
    """Ein Domain-Label beginnt oder endet mit einem Bindestrich."""

    label: str


@final
@dataclass(frozen=True, slots=True)
class EmailDomainLabelHasInvalidCharacters:
    """Ein Domain-Label enthaelt nicht erlaubte Zeichen - typisch ein Unterstrich."""

    label: str


@final
@dataclass(frozen=True, slots=True)
class EmailAddressLiteralInvalid:
    """Das Adress-Literal in eckigen Klammern ist keine gueltige IP-Adresse."""

    literal: str


@final
@dataclass(frozen=True, slots=True)
class UnencodableDomainLabel:
    """Ein internationalisiertes Label laesst sich nicht nach Punycode umwandeln.

    `reason` traegt den Wortlaut der IDN-Bibliothek. Das ist die eine Nutzlast in
    dieser Datei, die Fremdtext ist - die Bibliothek weiss genauer als wir, welche
    Unicode-Regel gebrochen wurde, und diese Auskunft wegzuwerfen waere schlechter,
    als sie durchzureichen.
    """

    label: str
    reason: str


type EmailError = (
    EmailHasWhitespace
    | EmailNeedsExactlyOneAtSign
    | EmailLocalPartMissing
    | EmailDomainMissing
    | EmailLocalPartTooLong
    | EmailLocalPartHasInvalidCharacters
    | EmailLocalPartHasMisplacedDot
    | EmailDomainTooLong
    | EmailDomainHasEmptyLabel
    | EmailDomainLabelTooLong
    | EmailDomainLabelHasEdgeHyphen
    | EmailDomainLabelHasInvalidCharacters
    | EmailAddressLiteralInvalid
    | UnencodableDomainLabel
)
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
