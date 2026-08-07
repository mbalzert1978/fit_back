"""Die Faelle des `DomainError`, die den Passwort-Hash betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
"""

from dataclasses import dataclass
from typing import final

__all__ = [
    "PasswordHashError",
    "PasswordHashIsEmpty",
]


@final
@dataclass(frozen=True, slots=True)
class PasswordHashIsEmpty:
    """Der Hasher hat keinen Wert geliefert - kein gueltige Hash-Eingabe."""


type PasswordHashError = PasswordHashIsEmpty
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
