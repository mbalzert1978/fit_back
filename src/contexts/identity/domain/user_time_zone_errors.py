"""Die Faelle des `DomainError`, die die Zeitzone betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
"""

from dataclasses import dataclass
from typing import final

__all__ = [
    "UserTimeZoneError",
    "UserTimeZoneUnknown",
]


@final
@dataclass(frozen=True, slots=True)
class UserTimeZoneUnknown:
    """Die Zeitzone ist in der IANA-Datenbank nicht bekannt."""

    candidate: str


type UserTimeZoneError = UserTimeZoneUnknown
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
