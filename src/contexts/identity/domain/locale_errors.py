"""Die Faelle des `DomainError`, die die Sprach-Kennung betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil der `DomainError`-**Summe**, die dort zusammengesetzt wird - der Liste,
gegen die die Fehlercode- und i18n-Drift-Pruefungen zaehlen. Warum die Faelle
dieses Moduls trotzdem ihre eigene, schmale Union bilden statt eines
Sammeltyps: docs/decisions/2026-08-17-0933-fehler-union-je-port-statt-domainerror-als-sammeltyp.md.
"""

from dataclasses import dataclass
from typing import ClassVar, final

__all__ = [
    "LocaleError",
    "LocaleIsEmpty",
    "LocaleNotSupported",
]


@final
@dataclass(frozen=True, slots=True)
class LocaleIsEmpty:
    """Es wurde gar keine Sprach-Kennung angegeben - nur Leerraum.

    Eigener Fall neben `LocaleNotSupported`: "die Sprache '   ' wird nicht
    unterstuetzt" zeigte auf nichts.
    """

    code: ClassVar[str] = "locale-is-empty"


@final
@dataclass(frozen=True, slots=True)
class LocaleNotSupported:
    """Die Sprach-Kennung wird vom Backend nicht unterstuetzt."""

    code: ClassVar[str] = "locale-not-supported"

    candidate: str


type LocaleError = LocaleIsEmpty | LocaleNotSupported
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
