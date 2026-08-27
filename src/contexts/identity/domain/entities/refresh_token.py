"""Aggregat RefreshToken - der abgelegte Anspruch, eine Sitzung zu verlaengern.

Ein eigenes Aggregat neben `User` (BACKEND.md Abschnitt 1) und kein Teil von
ihm: ein Nutzer hat viele davon, sie kommen und gehen ohne ihn, und keine
Regel muss ueber beide zugleich gelten. Der Verweis geht deshalb nur in **eine**
Richtung - der Token nennt seinen Nutzer, der Nutzer weiss von keinem Token.

Was hier steht, sind genau die Spalten von `identity.refresh_tokens`
(alembic/identity/versions/003_create_refresh_tokens_table.py). Widerruf und
Rotation (`revoked_at`, `replaced_by`) bekommen mit #52 ihren ersten Aufrufer
und werden erst dort modelliert.
"""

from typing import Final, final

from src.contexts.identity.domain.token_lifetimes import REFRESH_TOKEN_LIFETIME
from src.contexts.identity.domain.value_objects.refresh_token_id import RefreshTokenId
from src.contexts.identity.domain.value_objects.token_hash import TokenHash
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.shared_kernel import ConstructionKey, Timestamp, deny_foreign_key

__all__ = ["RefreshToken"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `issue` unten hat ihn."""


@final
class RefreshToken:
    """Ein ausgestellter Refresh-Token - identitaetsbasierte Gleichheit.

    Gebaut wird ausschliesslich ueber `issue`. Der Konstruktor prueft nichts
    mehr; er ist deren letzter Schritt und kein zweiter Weg herein.
    """

    def __init__(  # noqa: PLR0913 -- Aggregat: fuenf Value Objects, so viele wie Spalten
        self,
        token_id: RefreshTokenId,
        user_id: UserId,
        token_hash: TokenHash,
        issued_at: Timestamp,
        expires_at: Timestamp,
        *,
        key: ConstructionKey,
    ) -> None:
        """Setze den vollstaendigen Zustand aus bereits gueltigen Value Objects."""
        deny_foreign_key(key, _KEY)
        self.id = token_id
        self.user_id = user_id
        self.token_hash = token_hash
        self.issued_at = issued_at
        self.expires_at = expires_at

    @classmethod
    def issue(cls, user_id: UserId, token_hash: TokenHash, issued_at: Timestamp) -> RefreshToken:
        """Stelle einen Token fuer diesen Nutzer aus - der Ablauf steht hier.

        `issued_at` kommt herein und wird nicht von einer Uhr gelesen: es ist
        dieselbe Ablesung, aus der die Nutzer-Zeile entsteht. Eine zweite liesse
        Konto und Token um Sekunden auseinanderliegen.
        """
        return cls(
            RefreshTokenId.generate(),
            user_id,
            token_hash,
            issued_at,
            Timestamp(issued_at.unix_seconds + REFRESH_TOKEN_LIFETIME),
            key=_KEY,
        )

    @property
    def lifetime_seconds(self) -> int:
        """Wie lange dieser Token gilt - die Differenz, nicht die Konstante.

        Die Antwort nach aussen nennt diese Zahl. Sie hier auszurechnen statt
        die Konstante ein zweites Mal zu lesen heisst: was in der Ablage steht
        und was der Nutzer erfaehrt, koennen nicht auseinanderlaufen.
        """
        return self.expires_at.unix_seconds - self.issued_at.unix_seconds

    def __eq__(self, other: object) -> bool:
        """Vergleiche ueber die Identitaet, nicht ueber die Attribute."""
        return isinstance(other, RefreshToken) and self.id == other.id

    def __hash__(self) -> int:
        """Hashe ueber die Identitaet, passend zu `__eq__`."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Zeige Identitaet und Nutzer - nie den Abdruck."""
        return f"RefreshToken(id={self.id}, user_id={self.user_id})"
