"""Die Faelle des `DomainError`, die den Passwort-Hash betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil der `DomainError`-**Summe**, die dort zusammengesetzt wird - der Liste,
gegen die die Fehlercode- und i18n-Drift-Pruefungen zaehlen. Warum die Faelle
dieses Moduls trotzdem ihre eigene, schmale Union bilden statt eines
Sammeltyps: docs/decisions/2026-08-17-0933-fehler-union-je-port-statt-domainerror-als-sammeltyp.md.
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
