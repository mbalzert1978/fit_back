"""Value Object DisplayName - der Anzeigename des Users, 1-60 Zeichen."""

from dataclasses import dataclass
from typing import final

from src.shared_kernel import Err, Ok, Result

__all__ = ["MAXIMUM_LENGTH", "MINIMUM_LENGTH", "DisplayName"]

MINIMUM_LENGTH = 1
MAXIMUM_LENGTH = 60


@final
@dataclass(frozen=True, slots=True)
class DisplayName:
    """Getrimmter Anzeigename; die Invariante "nicht leer" gilt hier, nicht im User."""

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[DisplayName, str]:
        """Trimme und pruefe die Laenge einer moeglicherweise ungueltigen Eingabe."""
        trimmed = raw.strip()
        if not MINIMUM_LENGTH <= len(trimmed) <= MAXIMUM_LENGTH:
            return Err(f"Anzeigename muss {MINIMUM_LENGTH}-{MAXIMUM_LENGTH} Zeichen lang sein")
        return Ok(cls(trimmed))

    @classmethod
    def hydrate(cls, raw: str) -> DisplayName:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=display_name):
                return display_name
            case Err():
                raise AssertionError(f"unreachable: {raw!r} wurde vorgelagert validiert")
