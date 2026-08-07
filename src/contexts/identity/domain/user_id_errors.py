"""Die Faelle des `DomainError`, die die User-Identitaet betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
"""

from dataclasses import dataclass
from typing import final

__all__ = [
    "UserIdError",
    "UserIdMalformed",
]


@final
@dataclass(frozen=True, slots=True)
class UserIdMalformed:
    """Der User-Identitaet ist keine gueltige UUID."""

    candidate: str


type UserIdError = UserIdMalformed
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
