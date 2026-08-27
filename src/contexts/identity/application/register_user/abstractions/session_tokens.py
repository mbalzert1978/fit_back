"""Naht zur Sitzungsausstellung - drei Operationen, weil drei Dinge draussen sind.

Draussen bleibt genau das, was die Domaene nicht entscheiden kann: woher der
Zufall kommt, wie ein Abdruck gebildet wird, wohin die Zeile geht und wie
signiert wird. **Wie lange** ein Token gilt und **welche Felder** er traegt,
entscheidet die Domaene (`domain/value_objects/token_lifetime.py`,
`domain/entities/refresh_token.py`); die Gegenseite bekommt eine fertige Zeile
und schreibt sie.

Ein Vertrag und nicht drei, obwohl es drei Operationen sind: sie werden von
**einem** Mitspieler erfuellt - dem Aussteller. In der Produktion ist das
`PostgresSessionTokens`, in Specs `InMemorySessionTokens`.

Ueber die Naht wandern ausschliesslich Primitive: welches Verfahren signiert
(HS256) und welches den Abdruck bildet (SHA-256), geht den Slice nichts an.
"""

from dataclasses import dataclass, field
from typing import Protocol, final

__all__ = ["MintedSecret", "RefreshTokenRecord", "RegisterUserSessionTokens"]


@final
@dataclass(frozen=True, slots=True)
class MintedSecret:
    """Ein frisches Token-Geheimnis in seinen beiden Gestalten.

    Der Klartext geht nach aussen in die Antwort, der Abdruck in die Ablage.
    Beide entstehen zusammen und in einem Zug, weil nur die Gegenseite weiss,
    welches Verfahren den Abdruck bildet.

    Beide Felder tragen `repr=False`: sie sind Geheimnisse wie ein Passwort.
    """

    plaintext: str = field(repr=False)
    hashed: str = field(repr=False)


@final
@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    """Der zu schreibende Datensatz - flach und primitiv, kein Aggregat.

    `issued_at` und `expires_at` sind Unix-Sekunden (siehe
    `shared_kernel.Timestamp`), damit die Naht in jeder Engine gleich aussieht.
    Der Klartext des Token steht bewusst **nicht** darin.
    """

    token_id: str
    user_id: str
    token_hash: str = field(repr=False)
    issued_at: int
    expires_at: int


class RegisterUserSessionTokens(Protocol):
    """Naht zur Sitzungsausstellung."""

    def mint_secret(self) -> MintedSecret:
        """Erzeuge ein frisches Geheimnis und bilde seinen Abdruck."""
        ...

    async def store(self, record: RefreshTokenRecord) -> None:
        """Lege den fertigen Datensatz ab.

        Kein Ergebnistyp: es gibt keinen *erwarteten* Fehlschlag. Die Id ist
        frisch, der Abdruck ist eindeutig - was hier schiefgeht, ist ein
        Betriebsfall und faellt bis zur Middleware durch.
        """
        ...

    def sign_access_token(self, user_id: str, issued_at: int, expires_at: int) -> str:
        """Signiere den Access-Token fuer dieses Zeitfenster.

        Beide Zeitpunkte kommen herein und werden nicht drueben ausgerechnet.
        """
        ...
