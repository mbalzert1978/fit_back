"""Naht zur Access-Token-Signatur - eine Operation, ein Mitspieler.

Getrennt von `session_tokens.py`, weil es ein anderer Mitspieler ist: signiert
wird in der Produktion von `JwtAccessTokens`, abgelegt von
`PostgresSessionTokens`. Je Mitspieler ein eigener Vertrag - laegen beide in
einem, muesste der Ableger den Signierer nur durchreichen
(.rules/python/python-feature-slices.md, "Die Naht gehoert dem Use Case").

Ueber die Naht wandern ausschliesslich Primitive: welches Verfahren signiert
(HS256), geht den Slice nichts an.
"""

from typing import Protocol

__all__ = ["RegisterUserAccessTokens"]


class RegisterUserAccessTokens(Protocol):
    """Signiert Access-Token."""

    def sign(self, user_id: str, issued_at: int, expires_at: int) -> str:
        """Signiere den Access-Token fuer dieses Zeitfenster.

        Beide Zeitpunkte kommen herein und werden nicht drueben ausgerechnet.
        """
        ...
