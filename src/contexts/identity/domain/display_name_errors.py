"""Die Faelle des `DomainError`, die den Anzeigenamen betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
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
