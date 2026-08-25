"""Signiert Access-Token als JWT (HS256) - ueber `pyjwt`, nicht von Hand.

Kennt die Domaene nicht: Nutzer-Id und Zeitpunkt hinein, ein Token-String
heraus. Die Naht `RegisterUserSessionTokens` erfuellt
`postgres_session_tokens.py`, das dieses Modul benutzt.
"""

from typing import final

import jwt

__all__ = ["ACCESS_TOKEN_LIFETIME", "ALGORITHM", "JwtAccessTokens"]

ALGORITHM = "HS256"
"""Ein symmetrisches Verfahren, festgeschrieben statt aus dem Token gelesen.

Wer den Algorithmus beim Pruefen aus dem Token uebernimmt, laesst den Aufrufer
ihn waehlen - inklusive `none`. Deshalb steht er hier und wird beim Pruefen
(#52, #55) als erlaubte Liste uebergeben, nicht aus dem Header abgelesen.
"""

ACCESS_TOKEN_LIFETIME = 900
"""15 Minuten, BACKEND.md Abschnitt 8."""


@final
class JwtAccessTokens:
    """Stellt kurzlebige, signierte Access-Token aus."""

    def __init__(self, secret: str) -> None:
        """Nimm das Signaturgeheimnis entgegen - es kommt aus den Settings."""
        self._secret = secret

    def sign(self, user_id: str, issued_at: int) -> str:
        """Signiere ein Token fuer diesen Nutzer, gueltig ab `issued_at`.

        `sub`, `iat` und `exp` sind registrierte Claims aus RFC 7519 - eigene
        Namen dafuer zu erfinden hiesse, jede Bibliothek, die den Ablauf prueft,
        um diese Pruefung zu bringen.
        """
        return jwt.encode(
            {
                "sub": user_id,
                "iat": issued_at,
                "exp": issued_at + ACCESS_TOKEN_LIFETIME,
            },
            self._secret,
            algorithm=ALGORITHM,
        )
