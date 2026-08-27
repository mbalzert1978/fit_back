"""Wie lange die beiden Token gelten - eine Zahl, eine Stelle.

Beide standen bisher in der Infrastruktur (`jwt_access_tokens.py`,
`postgres_session_tokens.py`) und ein drittes Mal im Fake. Wie lange ein Zugang
gilt, ist aber eine fachliche Zusage aus BACKEND.md Abschnitt 0, Punkt 8 - kein
Detail des Signaturverfahrens und keines der Tabelle.
"""

from typing import Final

__all__ = ["ACCESS_TOKEN_LIFETIME", "REFRESH_TOKEN_LIFETIME"]

ACCESS_TOKEN_LIFETIME: Final = 900
"""15 Minuten in Sekunden."""

REFRESH_TOKEN_LIFETIME: Final = 5_184_000
"""60 Tage in Sekunden."""
