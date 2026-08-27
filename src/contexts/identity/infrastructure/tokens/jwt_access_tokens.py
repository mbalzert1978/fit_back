"""Signiert Access-Token als JWT (HS256) - ueber `pyjwt`, nicht von Hand.

Kennt die Domaene nicht: Nutzer-Id und Zeitfenster hinein, ein Token-String
heraus. **Wie lange** ein Zugang gilt, steht nicht hier, sondern in
`src/contexts/identity/domain/token_lifetimes.py`; der Aufrufer bringt den
Ablauf mit. Die Naht `RegisterUserSessionTokens` erfuellt
`postgres_session_tokens.py`, das dieses Modul benutzt.
"""

from typing import final

import jwt

__all__ = ["ALGORITHM", "JwtAccessTokens"]

ALGORITHM = "HS256"
"""Ein symmetrisches Verfahren, festgeschrieben statt aus dem Token gelesen.

Wer den Algorithmus beim Pruefen aus dem Token uebernimmt, laesst den Aufrufer
ihn waehlen - inklusive `none`. Deshalb steht er hier und wird beim Pruefen
(#52, #55) als erlaubte Liste uebergeben, nicht aus dem Header abgelesen.
"""


@final
class JwtAccessTokens:
    """Stellt kurzlebige, signierte Access-Token aus."""

    def __init__(self, secret: str) -> None:
        """Nimm das Signaturgeheimnis entgegen - es kommt aus den Settings."""
        self._secret = secret

    def sign(self, user_id: str, issued_at: int, expires_at: int) -> str:
        """Signiere ein Token fuer diesen Nutzer und dieses Zeitfenster.

        `sub`, `iat` und `exp` sind registrierte Claims aus RFC 7519 - eigene
        Namen dafuer zu erfinden hiesse, jede Bibliothek, die den Ablauf prueft,
        um diese Pruefung zu bringen.
        """
        return jwt.encode(
            {"sub": user_id, "iat": issued_at, "exp": expires_at},
            self._secret,
            algorithm=ALGORITHM,
        )
