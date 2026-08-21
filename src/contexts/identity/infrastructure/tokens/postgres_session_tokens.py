"""Erfuellt die Naht `RegisterUserSessionTokens`: signieren und ablegen.

Beides in einem, weil der Vertrag beides zusagt - ein herausgegebener
Refresh-Token, den niemand einloesen kann, waere eine Luege (Ticket #95).

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
from typing import final
from uuid import uuid7

from sqlalchemy import TextClause, text

from src.contexts.identity.application.register_user.abstractions import IssuedSession
from src.contexts.identity.infrastructure.persistence.user_store import UserStoreTransaction
from src.contexts.identity.infrastructure.tokens.jwt_access_tokens import (
    ACCESS_TOKEN_LIFETIME,
    JwtAccessTokens,
)

__all__ = ["REFRESH_TOKEN_LIFETIME", "PostgresSessionTokens"]

REFRESH_TOKEN_LIFETIME = 5_184_000
"""60 Tage in Sekunden, BACKEND.md Abschnitt 8."""

_TOKEN_BYTES = 32
"""256 Bit aus `secrets.token_urlsafe` - die Groesse, ab der Raten ausfaellt."""

_INSERT_REFRESH_TOKEN: TextClause = text("""
    INSERT INTO identity.refresh_tokens (id, user_id, token_hash, issued_at, expires_at)
    VALUES (:token_id, :user_id, :token_hash, :issued_at, :expires_at)
""")


def _hashed(token: str) -> str:
    """Bilde den Token auf seinen Ablage-Wert ab."""
    return hashlib.sha256(token.encode()).hexdigest()


@final
class PostgresSessionTokens:
    """Stellt die Sitzung aus und legt ihren Refresh-Token nach `identity.refresh_tokens`."""

    def __init__(self, transaction: UserStoreTransaction, access_tokens: JwtAccessTokens) -> None:
        """Nimm die laufende Transaktion des Vorgangs und den Signierer entgegen.

        **Dieselbe** Transaktion wie der Nutzer-Bestand: Nutzer-Zeile und
        Refresh-Token werden gemeinsam sichtbar oder gar nicht. Ein Token zu
        einem Konto, das es nicht gibt, waere sonst ein moeglicher Zustand.
        """
        self._transaction = transaction
        self._access_tokens = access_tokens

    async def issue(self, user_id: str, issued_at: int) -> IssuedSession:
        """Signiere den Access-Token, erzeuge den Refresh-Token und lege ihn ab."""
        refresh_token = secrets.token_urlsafe(_TOKEN_BYTES)
        await self._transaction.execute(
            _INSERT_REFRESH_TOKEN,
            {
                "token_id": str(uuid7()),
                "user_id": user_id,
                "token_hash": _hashed(refresh_token),
                "issued_at": issued_at,
                "expires_at": issued_at + REFRESH_TOKEN_LIFETIME,
            },
        )
        return IssuedSession(
            access_token=self._access_tokens.sign(user_id, issued_at),
            expires_in=ACCESS_TOKEN_LIFETIME,
            refresh_token=refresh_token,
            refresh_expires_in=REFRESH_TOKEN_LIFETIME,
        )
