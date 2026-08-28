"""Value Object TokenLifetimes - die beiden Geltungsdauern als *ein* Wert.

Access und Refresh reisten vorher als zwei gleichnamige `TokenLifetime` durch
Fabrik, Handler und Ausstellung - positional und still vertauschbar
(docs/decisions/2026-08-28-1450-der-handler-orchestriert-die-ausstellung.md).
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["TokenLifetimes"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class TokenLifetimes:
    """Wie lange der Zugang gilt und wie lange das Recht, ihn zu erneuern."""

    access: TokenLifetime
    refresh: TokenLifetime
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(cls, *, access_seconds: int, refresh_seconds: int) -> Self:
        """Nimm beide geprueften Dauern der Konfiguration an - benannt, nie positional."""
        return cls(
            TokenLifetime.hydrate(access_seconds),
            TokenLifetime.hydrate(refresh_seconds),
            key=_KEY,
        )
