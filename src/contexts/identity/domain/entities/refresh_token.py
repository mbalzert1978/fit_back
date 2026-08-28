"""Aggregat RefreshToken - der abgelegte Anspruch, eine Sitzung zu verlaengern.

Warum ein eigenes Aggregat neben `User`:
docs/decisions/2026-08-27-1830-refresh-token-ist-ein-aggregat.md.

Ausgestellt wird ausschliesslich hier: `issue` bekommt die Geheimnis-Quelle
hereingereicht, zieht sein Geheimnis selbst, behaelt dessen Abdruck und gibt
dessen Klartext zurueck. Kein Aufrufer sieht das Geheimnis vor dem Aggregat, und
keiner kann einen Abdruck ablegen und einen anderen Klartext ausgeben
(docs/decisions/2026-08-28-0930-das-aggregat-zieht-sein-geheimnis-selbst.md).

Was hier steht, sind genau die Spalten von `identity.refresh_tokens`
(alembic/identity/versions/003_create_refresh_tokens_table.py). Widerruf und
Rotation (`revoked_at`, `replaced_by`) bekommen mit #53 ihren ersten Aufrufer
und werden erst dort modelliert.
"""

from dataclasses import dataclass, field
from typing import Final, final

from src.contexts.identity.domain.ports.token_secrets import TokenSecrets
from src.contexts.identity.domain.value_objects.credentials import Grant
from src.contexts.identity.domain.value_objects.refresh_token_id import RefreshTokenId
from src.contexts.identity.domain.value_objects.token_hash import TokenHash
from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.shared_kernel import ConstructionKey, Timestamp, deny_foreign_key

__all__ = ["RefreshToken", "RefreshTokenIssuance"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `issue` unten hat ihn."""


@final
class RefreshToken:
    """Ein ausgestellter Refresh-Token - identitaetsbasierte Gleichheit.

    Gebaut wird ausschliesslich ueber `issue`. Zustandswechsel entstehen als
    **neues** Aggregat mit derselben Identitaet, nicht durch Mutation
    (docs/decisions/2026-08-27-2120-entitaeten-wechseln-ihren-zustand-als-neue-instanz.md).

    Der Klartext des Geheimnisses ist **kein Feld** dieses Aggregats. Er kann
    deshalb auf keinem Weg in eine abgelegte Zeile geraten.
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
    def issue(
        cls,
        user_id: UserId,
        secrets: TokenSecrets,
        issued_at: Timestamp,
        lifetime: TokenLifetime,
    ) -> RefreshTokenIssuance:
        """Stelle einen Token fuer diesen Nutzer aus - Aggregat und Klartext in einem.

        Die Quelle des Geheimnisses wird **in die Methode** hereingereicht, nie
        in ein Feld: ein Aggregat, das seine Mitspieler behaelt, ist keines mehr.
        Gezogen wird hier, geteilt auch: der Abdruck bleibt im Aggregat, der
        Klartext geht als `Grant` an den Aufrufer, und beide verlassen die
        Ausstellung nur gemeinsam.

        `issued_at` kommt herein und wird nicht von einer Uhr gelesen: es ist
        dieselbe Ablesung, aus der die Nutzer-Zeile entsteht.
        """
        secret = secrets.mint()
        return RefreshTokenIssuance(
            cls(
                RefreshTokenId.generate(),
                user_id,
                secret.token_hash,
                issued_at,
                lifetime.expires_from(issued_at),
                key=_KEY,
            ),
            Grant.hydrate(secret.plaintext, lifetime),
            key=_KEY,
        )

    def __eq__(self, other: object) -> bool:
        """Vergleiche ueber die Identitaet, nicht ueber die Attribute."""
        return isinstance(other, RefreshToken) and self.id == other.id

    def __hash__(self) -> int:
        """Hashe ueber die Identitaet, passend zu `__eq__`."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Zeige Identitaet und Nutzer - nie den Abdruck."""
        return f"RefreshToken(id={self.id}, user_id={self.user_id})"


@final
@dataclass(frozen=True, slots=True)
class RefreshTokenIssuance:
    """Was eine Ausstellung hergibt: das abzulegende Aggregat und die Ausgabe.

    Ein eigener Typ und kein `tuple`: die beiden gehoeren zusammen, und nur
    `RefreshToken.issue` darf sie paaren. Wer die Ausgabe will, bekommt damit
    zwangslaeufig das Aggregat, dessen Abdruck zu ihrem Klartext passt.
    """

    refresh_token: RefreshToken
    grant: Grant
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jede Paarung ab, die nicht durch `RefreshToken.issue` ging."""
        deny_foreign_key(self.key, _KEY)
