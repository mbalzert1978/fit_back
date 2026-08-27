"""Value Object IssuedCredentials - was der Nutzer bei der Aufnahme mitbekommt.

Bewusst **kein** Aggregat und bewusst nicht "die Sitzung": hier steht der
Refresh-Token im **Klartext**, und der wird nie abgelegt. Was abgelegt wird, ist
das Aggregat `RefreshToken` - Id, Nutzer, Abdruck, Ablauf. Beides trug frueher
denselben Namen `Session` und war damit zweierlei unter einem Wort.

Kein `parse` neben `hydrate`: die vier Werte entstehen beim Aussteller und sonst
nirgends. Die Sperre steht trotzdem - Zugangsdaten entstehen ausschliesslich
ueber `hydrate`, niemand sonst im Code kann welche erfinden.
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["IssuedCredentials"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class IssuedCredentials:
    """Access- und Refresh-Token samt ihren Lebensdauern in Sekunden.

    Beide Token tragen `repr=False`: sie sind Geheimnisse wie ein Passwort und
    haben in keinem Log und keiner Fehlermeldung etwas zu suchen.
    """

    access_token: str = field(repr=False)
    expires_in: int
    refresh_token: str = field(repr=False)
    refresh_expires_in: int
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(
        cls,
        access_token: str,
        expires_in: int,
        refresh_token: str,
        refresh_expires_in: int,
    ) -> Self:
        """Nimm die Werte des Ausstellers an - er ist die einzige Quelle."""
        return cls(
            access_token,
            expires_in,
            refresh_token,
            refresh_expires_in,
            key=_KEY,
        )
