"""Value Object TokenLifetime - wie lange ein ausgestellter Token gilt.

Nimmt eine bereits geprueffte Zahl an: **ob** eine Geltungsdauer zulaessig ist,
entscheidet die Konfiguration des Prozesses (`src/settings.py`, `TokenSettings`)
und nicht die Domaene - es ist keine Geschaeftsinvariante, sondern eine
Einstellung
(docs/decisions/2026-08-27-1930-geltungsdauern-sind-konfiguration-nicht-domaene.md).

Was hier bleibt, gehoert der Domaene: **dass** ein Token eine Geltungsdauer hat,
und **wann** er damit ablaeuft.
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.shared_kernel import ConstructionKey, Timestamp, deny_foreign_key

__all__ = ["TokenLifetime"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class TokenLifetime:
    """Eine Geltungsdauer in Sekunden, aus vertrauenswuerdiger Quelle."""

    seconds: int
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(cls, seconds: int) -> Self:
        """Nimm die geprueffte Dauer der Konfiguration an."""
        return cls(seconds, key=_KEY)

    def expires_from(self, issued_at: Timestamp) -> Timestamp:
        """Der Ablauf dieser Dauer hinter `issued_at` - die eine Rechnung."""
        return Timestamp(issued_at.unix_seconds + self.seconds)
