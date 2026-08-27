"""Die Faelle des `DomainError`, die die Zeitzone betreffen.

Physisch getrennt von [`errors.py`](./errors.py), fachlich **nicht**: sie sind
Teil der `DomainError`-**Summe**, die dort zusammengesetzt wird - der Liste,
gegen die die Fehlercode- und i18n-Drift-Pruefungen zaehlen. Warum die Faelle
dieses Moduls trotzdem ihre eigene, schmale Union bilden statt eines
Sammeltyps: docs/decisions/2026-08-17-0933-fehler-union-je-port-statt-domainerror-als-sammeltyp.md.
"""

from dataclasses import dataclass
from typing import ClassVar, final

__all__ = [
    "UserTimeZoneError",
    "UserTimeZoneIsEmpty",
    "UserTimeZoneUnknown",
]


@final
@dataclass(frozen=True, slots=True)
class UserTimeZoneIsEmpty:
    """Es wurde gar keine Zeitzone angegeben - nur Leerraum.

    Eigener Fall neben `UserTimeZoneUnknown`: "gar nichts angegeben" und "das
    kenne ich nicht" sind zwei Auskuenfte, und nur die zweite kann einen Wert
    nennen.
    """

    code: ClassVar[str] = "user-time-zone-is-empty"


@final
@dataclass(frozen=True, slots=True)
class UserTimeZoneUnknown:
    """Die Zeitzone ist in der IANA-Datenbank nicht bekannt."""

    code: ClassVar[str] = "user-time-zone-unknown"

    candidate: str


type UserTimeZoneError = UserTimeZoneIsEmpty | UserTimeZoneUnknown
"""Teil-Union - zusammengefuehrt zum einen `DomainError` in `errors.py`."""
