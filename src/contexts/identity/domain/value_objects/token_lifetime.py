"""Value Object TokenLifetime - wie lange ein ausgestellter Token gilt.

Die Ober- und Untergrenzen stehen hier und nirgends sonst
(docs/decisions/2026-08-27-2115-die-obergrenze-der-geltungsdauer-steht-in-der-domaene.md).
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.shared_kernel import ConstructionKey, Timestamp, deny_foreign_key

__all__ = [
    "ACCESS_TOKEN_MAXIMUM_SECONDS",
    "REFRESH_TOKEN_MAXIMUM_SECONDS",
    "TokenLifetime",
]

ACCESS_TOKEN_MAXIMUM_SECONDS = 900
"""15 Minuten - die Zusage aus BACKEND.md Abschnitt 0, Punkt 8, als Obergrenze."""

REFRESH_TOKEN_MAXIMUM_SECONDS = 5_184_000
"""60 Tage - dieselbe Zusage."""

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `access` und `refresh` unten haben ihn."""


def _within(seconds: int, maximum: int) -> int:
    """Gib die Dauer zurueck, wenn sie im erlaubten Fenster liegt."""
    if not 0 < seconds <= maximum:
        msg = f"Token lifetime must be between 1 and {maximum} seconds, got {seconds}"
        raise ValueError(msg)
    return seconds


@final
@dataclass(frozen=True, slots=True)
class TokenLifetime:
    """Eine geprueffte Geltungsdauer in Sekunden.

    Kein `Result` und kein Fehlertyp: der Wert kommt aus der Konfiguration des
    Prozesses, ein falscher ist kein Fachfall, sondern eine Fehlbedienung.
    """

    seconds: int
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `access` oder `refresh` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def access(cls, seconds: int) -> Self:
        """Nimm die Geltungsdauer eines Access-Token an."""
        return cls(_within(seconds, ACCESS_TOKEN_MAXIMUM_SECONDS), key=_KEY)

    @classmethod
    def refresh(cls, seconds: int) -> Self:
        """Nimm die Geltungsdauer eines Refresh-Token an."""
        return cls(_within(seconds, REFRESH_TOKEN_MAXIMUM_SECONDS), key=_KEY)

    def expires_from(self, issued_at: Timestamp) -> Timestamp:
        """Der Ablauf dieser Dauer hinter `issued_at` - die eine Rechnung."""
        return Timestamp(issued_at.unix_seconds + self.seconds)
