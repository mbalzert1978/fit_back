"""Value Object Email - case-insensitiv normalisierte, eindeutige E-Mail-Adresse."""

import re
from dataclasses import dataclass
from typing import final

from src.shared_kernel import Err, Ok, Result

__all__ = ["Email"]

_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@final
@dataclass(frozen=True, slots=True)
class Email:
    """Bereits normalisierte E-Mail-Adresse (getrimmt, case-folded).

    Die Normalisierung passiert in `parse` und nirgends sonst - damit ist die
    Eindeutigkeitspruefung des Registry-Ports zwangslaeufig case-insensitiv.
    """

    value: str

    @classmethod
    def parse(cls, raw: str) -> Result[Email, str]:
        """Normalisiere und pruefe eine moeglicherweise ungueltige Eingabe."""
        normalized = raw.strip().casefold()
        if not _SHAPE.match(normalized):
            return Err(f"keine gueltige E-Mail-Adresse: {raw!r}")
        return Ok(cls(normalized))

    @classmethod
    def hydrate(cls, raw: str) -> Email:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=email):
                return email
            case Err():
                raise AssertionError(f"unreachable: {raw!r} wurde vorgelagert validiert")
