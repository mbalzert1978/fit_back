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
    "ExtraForbidden",
    "FieldRequired",
    "FieldTypeError",
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


type RequestValidationFault = FieldRequired | FieldTypeError | ExtraForbidden | JsonInvalid
"""Union der strukturellen Request-Validierungsfehler.

`Fault` und nicht `Error`: `fastapi.exceptions.RequestValidationError` heisst schon so und
wird im selben Paket verwendet (`exception_handlers.py`). Zwei verschiedene Dinge unter
einem Namen laden zu einem Import-Versehen ein, das keine Fehlermeldung erzeugt - der
eine Name loest den anderen einfach ab.
"""
