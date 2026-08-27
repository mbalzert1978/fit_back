"""Erfuellt die Naht `RegisterUserSessionTokens`: Geheimnis, Ablage, Signatur.

Was hier passiert, ist ausschliesslich Handwerk: Zufall ziehen, Abdruck bilden,
eine **fertige** Zeile schreiben, ein Token signieren. Welche Felder die Zeile
traegt und wie lange ein Token gilt, entscheidet die Domaene
(`domain/entities/refresh_token.py`, `domain/value_objects/token_lifetime.py`).

Der Refresh-Token verlaesst dieses Modul im Klartext nach **aussen** und geht im
**Hash** in die Datenbank. Der Klartext ist ein Geheimnis wie ein Passwort: wer
die Tabelle liest, koennte sich sonst als jeder Nutzer ausgeben. Zum Einloesen
(#52) reicht der Hash - der Aufrufer bringt den Klartext mit.

SHA-256 und nicht Argon2id: anders als ein Passwort ist dieser Token 256 Bit
Zufall aus `secrets`, es gibt also nichts zu erraten, wogegen ein langsames
Verfahren schuetzen muesste.
"""

import hashlib
import secrets
from typing import Final, final

from sqlalchemy import TextClause, text

from src.contexts.identity.application.register_user.abstractions import (
    MintedSecret,
    RefreshTokenRecord,
)
from src.contexts.identity.infrastructure.persistence.user_store import UserStoreTransaction
from src.contexts.identity.infrastructure.tokens.jwt_access_tokens import JwtAccessTokens

__all__ = ["PostgresSessionTokens"]

_TOKEN_BYTES: Final = 32
"""256 Bit aus `secrets.token_urlsafe` - die Groesse, ab der Raten ausfaellt."""

_INSERT_REFRESH_TOKEN: TextClause = text("""
    INSERT INTO identity.refresh_tokens (id, user_id, token_hash, issued_at, expires_at)
    VALUES (:token_id, :user_id, :token_hash, :issued_at, :expires_at)
""")


@final
class PostgresSessionTokens:
    """Stellt Geheimnisse aus und legt Refresh-Token nach `identity.refresh_tokens`."""

    def __init__(self, transaction: UserStoreTransaction, access_tokens: JwtAccessTokens) -> None:
        """Nimm die laufende Transaktion des Vorgangs und den Signierer entgegen.

        **Dieselbe** Transaktion wie der Nutzer-Bestand: Nutzer-Zeile und
        Refresh-Token werden gemeinsam sichtbar oder gar nicht. Ein Token zu
        einem Konto, das es nicht gibt, waere sonst ein moeglicher Zustand.
        """
        self._transaction = transaction
        self._access_tokens = access_tokens

    def mint_secret(self) -> MintedSecret:
        """Ziehe 256 Bit Zufall und bilde seinen SHA-256-Abdruck."""
        plaintext = secrets.token_urlsafe(_TOKEN_BYTES)
        return MintedSecret(
            plaintext=plaintext,
            hashed=hashlib.sha256(plaintext.encode()).hexdigest(),
        )

    async def store(self, record: RefreshTokenRecord) -> None:
        """Schreibe die fertige Zeile - hier wird nichts mehr ausgerechnet."""
        await self._transaction.execute(
            _INSERT_REFRESH_TOKEN,
            {
                "token_id": record.token_id,
                "user_id": record.user_id,
                "token_hash": record.token_hash,
                "issued_at": record.issued_at,
                "expires_at": record.expires_at,
            },
        )

    def sign_access_token(self, user_id: str, issued_at: int, expires_at: int) -> str:
        """Reiche das Zeitfenster an den Signierer durch."""
        return self._access_tokens.sign(user_id, issued_at, expires_at)
