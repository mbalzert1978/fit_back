"""Die Faelle des `DomainError`, die das Passwort betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil der `DomainError`-**Summe**, die dort zusammengesetzt wird - der Liste,
gegen die die Fehlercode- und i18n-Drift-Pruefungen zaehlen. Warum die Faelle
dieses Moduls trotzdem ihre eigene, schmale Union bilden statt eines
Sammeltyps: docs/decisions/2026-08-17-0933-fehler-union-je-port-statt-domainerror-als-sammeltyp.md.
"""

from dataclasses import dataclass
from typing import ClassVar, final

__all__ = [
    "PasswordError",
    "PasswordTooLong",
    "PasswordTooShort",
]


@final
@dataclass(frozen=True, slots=True)
class PasswordTooShort:
    """Das Passwort unterschreitet die Mindestlaenge."""

    code: ClassVar[str] = "password-too-short"

    actual_length: int
    minimum: int


@final
@dataclass(frozen=True, slots=True)
class PasswordTooLong:
    """Das Passwort ueberschreitet die zulaessige Hoechstlaenge."""

    code: ClassVar[str] = "password-too-long"

    actual_length: int
    maximum: int


type PasswordError = PasswordTooShort | PasswordTooLong
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
