"""Die Faelle des `DomainError`, die die Sprach-Kennung betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil der `DomainError`-**Summe**, die dort zusammengesetzt wird - der Liste,
gegen die die Fehlercode- und i18n-Drift-Pruefungen zaehlen. Das eine `E`, das
ein Port spricht, ist sie seit Stufe 4 von Ticket 0011 nicht mehr: die Faelle
dieses Moduls bilden die eigene, schmale Union der Operation, die sie erzeugt.
"""

from dataclasses import dataclass
from typing import ClassVar, final

__all__ = [
    "LocaleError",
    "LocaleNotSupported",
]


@final
@dataclass(frozen=True, slots=True)
class LocaleNotSupported:
    """Die Sprach-Kennung wird vom Backend nicht unterstuetzt."""

    code: ClassVar[str] = "locale-not-supported"

    candidate: str


type LocaleError = LocaleNotSupported
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
