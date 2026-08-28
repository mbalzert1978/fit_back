"""Value Object TokenHash - der Ablage-Wert eines Refresh-Token.

Der Klartext reist durch die Domaene (`TokenSecret`, `Grant`), aber nie in eine
Zeile: abgelegt wird ausschliesslich dieser Abdruck
(docs/decisions/2026-08-21-2230-pyjwt-hinter-der-naht-refresh-token-als-hash.md,
docs/decisions/2026-08-28-0807-das-aggregat-stellt-sich-selbst-aus.md).
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["TokenHash"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class TokenHash:
    """Der Abdruck eines Refresh-Token, so wie er in der Ablage steht.

    Kein `parse`: welches Verfahren den Abdruck bildet, entscheidet die Seite,
    die ihn bildet - die Domaene hat daran nichts zu pruefen. Die Sperre steht
    trotzdem, damit ein Abdruck nur ueber `hydrate` entstehen kann.

    `repr=False`: ein Abdruck ist zwar nicht der Token, gehoert aber trotzdem in
    kein Log.
    """

    value: str = field(repr=False)
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(cls, raw: str) -> Self:
        """Nimm den Abdruck an, den die Gegenseite gebildet hat."""
        return cls(raw, key=_KEY)
