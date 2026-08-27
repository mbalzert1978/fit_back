"""Value Object Session - die ausgestellte Sitzung auf der Innenseite.

Das Gegenstueck zu `IssuedSession` der public Naht: dieselben vier Werte, aber
innen. Damit kreuzt kein Naht-Typ mehr die Grenze zum Handler
(.rules/python/python-feature-slices.md, "kein DTO kreuzt die Grenze zum
Handler").

Sie ist **nicht Teil des `User`-Aggregats** - `User` weiss nichts von Tokens -
und verweist ueber die Nutzer-Id auf ihn. Der Refresh-Token dahinter ist ein
eigenes Aggregat (BACKEND.md Abschnitt 1, `RefreshToken`); modelliert wird es
erst, wenn Einloesen und Widerruf gebaut werden. `register_user` laesst ihn nur
ausstellen und laedt oder aendert keinen.

Kein `parse` neben `hydrate`: die vier Werte entstehen beim Aussteller und
sonst nirgends. Es gibt an ihnen nichts, was die Domaene beurteilen koennte -
wie lange ein Token gilt, entscheidet, wer ihn signiert. Die Sperre steht
trotzdem, und zwar genau dafuer: eine Sitzung entsteht ausschliesslich ueber
`hydrate`, niemand sonst im Code kann eine erfinden.
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["Session"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class Session:
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
