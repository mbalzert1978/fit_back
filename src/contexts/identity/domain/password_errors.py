"""Die Faelle des `DomainError`, die das Passwort betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
"""

from dataclasses import dataclass
from typing import final

__all__ = [
    "PasswordError",
    "PasswordTooShort",
]


@final
@dataclass(frozen=True, slots=True)
class PasswordTooShort:
    """Das Passwort unterschreitet die Mindestlaenge."""

    actual_length: int
    minimum: int


type PasswordError = PasswordTooShort
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
