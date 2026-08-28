"""Value Object TokenSecret - die zwei Gestalten *eines* Geheimnisses.

Der Klartext geht nach aussen in die Antwort, der Abdruck in die Ablage. Dass
die beiden zusammengehoeren, entscheidet die Domaene - und dieser Typ ist die
einzige Stelle, an der sie zusammengefuegt werden
(docs/decisions/2026-08-28-0807-das-aggregat-stellt-sich-selbst-aus.md).

Gebildet werden beide draussen: woher der Zufall kommt und welches Verfahren den
Abdruck bildet, entscheidet die Domaene weiterhin nicht.
"""

from dataclasses import dataclass, field
from typing import Final, Self, final

from src.contexts.identity.domain.value_objects.token_hash import TokenHash
from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["TokenSecret"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class TokenSecret:
    """Ein frisches Geheimnis als Klartext und Abdruck.

    Kein `parse`: geprueft wird hier nichts, gepaart schon. Wer die beiden
    Haelften trennt, muss durch `RefreshToken.issue` - das Aggregat behaelt den
    Abdruck und gibt den Klartext weiter.

    `plaintext` traegt `repr=False`: er ist ein Geheimnis wie ein Passwort.
    """

    plaintext: str = field(repr=False)
    token_hash: TokenHash
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(cls, plaintext: str, hashed: str) -> Self:
        """Nimm die beiden Haelften an, die die Gegenseite in einem Zug bildete."""
        return cls(plaintext, TokenHash.hydrate(hashed), key=_KEY)
