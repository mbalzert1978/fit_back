"""Strukturelle Request-Validierungsfehler (Pydantic) als Tagged Union mit Codes.

Diese Fehler entstehen am HTTP-Rand aus schema mismatches, nicht aus fachlicher
Validierung. Sie folgen demselben Muster wie Slice-Fehler: geschlossene Union
mit explizitem `code` Attribute pro Fall.

`RegisterUserBody` hat fünf `str`-Pflichtfelder und `extra="forbid"`, keine
eigenen Constraints. Die erreichbaren Fälle sind daher:
- Missing required field
- Wrong field type (e.g., dict statt string)
- Extra forbidden field
- JSON unparseable

Feld-Parameter sind Teil der Nutzlast, nicht des Codes — so bleibt die
Textvorlage sprachunabhängig.
"""

from dataclasses import dataclass
from typing import ClassVar, final

__all__ = [
    "BodyNotAnObject",
    "ExtraForbidden",
    "FieldRequired",
    "FieldTypeError",
    "FieldValueRejected",
    "JsonInvalid",
    "RequestValidationFault",
]


@final
@dataclass(frozen=True, slots=True)
class FieldRequired:
    """Ein erforderliches Feld fehlt in der Anfrage."""

    code: ClassVar[str] = "field-required"
    field: str
    """Der Name des fehlenden Feldes."""


@final
@dataclass(frozen=True, slots=True)
class FieldTypeError:
    """Ein Feld hat den falschen Typ (z.B. dict statt string, number statt string)."""

    code: ClassVar[str] = "field-type-error"
    field: str
    """Der Name des Feldes mit falschem Typ."""
    expected: str = "string"
    """Der erwartete Typ (fast immer 'string' für RegisterUserBody)."""


@final
@dataclass(frozen=True, slots=True)
class ExtraForbidden:
    """Ein Feld existiert nicht in der erwarteten Struktur (extra="forbid")."""

    code: ClassVar[str] = "extra-forbidden"
    field: str
    """Der Name des unbekannten Feldes."""


@final
@dataclass(frozen=True, slots=True)
class JsonInvalid:
    """Der Request-Body ist kein gültiges JSON."""

    code: ClassVar[str] = "json-invalid"


@final
@dataclass(frozen=True, slots=True)
class BodyNotAnObject:
    """Der Body ist gültiges JSON, aber kein Objekt — etwa ein Array oder ein String.

    Eigener Fall statt `FieldTypeError`: dieser Fehler betrifft kein Feld, und der
    frühere Auffangzweig hat ihn mit leerem Feldnamen als „das Feld '' hat den
    falschen Typ" beantwortet.

    Pydantic meldet ihn über FastAPIs Body-Validierung als `model_attributes_type`
    — nicht als `model_type`, was das Modell allein gefahren liefert. Gemessen in
    `tests/api/test_pydantic_error_contract.py`, nicht angenommen.
    """

    code: ClassVar[str] = "body-not-an-object"


@final
@dataclass(frozen=True, slots=True)
class FieldValueRejected:
    """Ein Pydantic-`field_validator` hat den Wert abgelehnt (`value_error`).

    Die Modelle dieses Repos tragen bewusst keine eigenen Constraints — fachliche
    Prüfung gehört in den Slice, nicht ins DTO. Der Exception-Handler hängt aber
    app-weit und sieht jedes Modell, also ist der Fall erreichbar.

    Pydantics eigener Meldungstext wird **nicht** durchgereicht: er ist englisch,
    unabhängig vom `Accept-Language`-Header. Der Aufrufer bekommt stattdessen den
    übersetzten Text zu diesem Code.
    """

    code: ClassVar[str] = "field-value-rejected"
    field: str
    """Der Name des abgelehnten Feldes."""


type RequestValidationFault = (
    FieldRequired
    | FieldTypeError
    | ExtraForbidden
    | JsonInvalid
    | BodyNotAnObject
    | FieldValueRejected
)
"""Union der strukturellen Request-Validierungsfehler.

`Fault` und nicht `Error`: `fastapi.exceptions.RequestValidationError` heisst schon so und
wird im selben Paket verwendet (`exception_handlers.py`). Zwei verschiedene Dinge unter
einem Namen laden zu einem Import-Versehen ein, das keine Fehlermeldung erzeugt - der
eine Name loest den anderen einfach ab.
"""
