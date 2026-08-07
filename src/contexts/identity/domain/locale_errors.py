"""Die Faelle des `DomainError`, die die Sprach-Kennung betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil derselben einen, flachen `DomainError`-Union, die dort zusammengesetzt wird.
"""

from dataclasses import dataclass
from typing import final

__all__ = [
    "LocaleError",
    "LocaleNotSupported",
]


@final
@dataclass(frozen=True, slots=True)
class LocaleNotSupported:
    """Die Sprach-Kennung wird vom Backend nicht unterstuetzt."""

    candidate: str


type LocaleError = LocaleNotSupported
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
