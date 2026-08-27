"""Value Object TokenHash - der Ablage-Wert eines Refresh-Token.

Der Klartext des Token kommt hier nie an. Er geht vom Aussteller direkt nach
aussen und in die Antwort; abgelegt wird ausschliesslich sein Hash
(docs/decisions/2026-08-21-2230-pyjwt-hinter-der-naht-refresh-token-als-hash.md).
Die Domaene kennt deshalb nur diese Haelfte.
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
