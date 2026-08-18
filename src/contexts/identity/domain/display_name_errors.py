"""Die Faelle des `DomainError`, die den Anzeigenamen betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil der `DomainError`-**Summe**, die dort zusammengesetzt wird - der Liste,
gegen die die Fehlercode- und i18n-Drift-Pruefungen zaehlen. Das eine `E`, das
ein Port spricht, ist sie seit Stufe 4 von Ticket 0011 nicht mehr: die Faelle
dieses Moduls bilden die eigene, schmale Union der Operation, die sie erzeugt.
"""

from dataclasses import dataclass
from typing import ClassVar, final

__all__ = [
    "DisplayNameError",
    "DisplayNameIsEmpty",
    "DisplayNameTooLong",
]


@final
@dataclass(frozen=True, slots=True)
class DisplayNameIsEmpty:
    """Der Anzeigename ist leer oder besteht nur aus Leerraum.

    Eigener Fall, obwohl die Pruefung selbst aus `NotEmptyString` im Shared Kernel
    kommt: `TextIsEmpty` ist dort ein technischer Fall ohne Feldbezug und traegt
    deshalb keinen Code. Waere er hier stehengeblieben, muesste ein und derselbe
    Fall je nach Feld einen anderen Code liefern - und der Code gehoert laut
    `shared_kernel/coded_error.py` genau einmal an genau einen Fall. `DisplayName.parse`
    uebersetzt darum an der Grenze.
    """

    code: ClassVar[str] = "display-name-is-empty"


@final
@dataclass(frozen=True, slots=True)
class DisplayNameTooLong:
    """Der Anzeigename ueberschreitet die zulaessige Laenge."""

    code: ClassVar[str] = "display-name-too-long"

    actual_length: int
    maximum: int


type DisplayNameError = DisplayNameIsEmpty | DisplayNameTooLong
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
