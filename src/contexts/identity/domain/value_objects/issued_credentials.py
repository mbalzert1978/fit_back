"""Value Object IssuedCredentials - was der Nutzer bei der Aufnahme mitbekommt.

Hier steht der Refresh-Token im **Klartext**, und der wird nie abgelegt; was
abgelegt wird, ist das Aggregat `RefreshToken`
(docs/decisions/2026-08-27-1830-refresh-token-ist-ein-aggregat.md).

Kein `parse` neben `hydrate`: die vier Werte entstehen beim Aussteller und sonst
nirgends.
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["IssuedCredentials"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class IssuedCredentials:
    """Access- und Refresh-Token samt ihren Geltungsdauern.

    Die beiden Dauern sind `TokenLifetime` und keine nackten `int`: die Domaene
    spricht Value Objects, die Sekunden fallen erst im Response-Mapper heraus
    (.rules/python/python-feature-slices.md).

    Beide Token tragen `repr=False`: sie sind Geheimnisse wie ein Passwort und
    haben in keinem Log und keiner Fehlermeldung etwas zu suchen.
    """

    access_token: str = field(repr=False)
    access_lifetime: TokenLifetime
    refresh_token: str = field(repr=False)
    refresh_lifetime: TokenLifetime
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(
        cls,
        access_token: str,
        access_lifetime: TokenLifetime,
        refresh_token: str,
        refresh_lifetime: TokenLifetime,
    ) -> Self:
        """Nimm die Werte des Ausstellers an - er ist die einzige Quelle."""
        return cls(
            access_token,
            access_lifetime,
            refresh_token,
            refresh_lifetime,
            key=_KEY,
        )
