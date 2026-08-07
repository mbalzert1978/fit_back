"""Die Faelle des `DomainError`, die den Anzeigenamen betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
"""

from dataclasses import dataclass
from typing import final

__all__ = [
    "DisplayNameError",
    "DisplayNameTooLong",
]


@final
@dataclass(frozen=True, slots=True)
class DisplayNameTooLong:
    """Der Anzeigename ueberschreitet die zulaessige Laenge."""

    actual_length: int
    maximum: int


type DisplayNameError = DisplayNameTooLong
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
