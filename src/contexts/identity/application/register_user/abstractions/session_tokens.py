"""Naht zur Sitzungsausstellung - eine Operation, weil es eine gibt.

Ausstellen heisst hier **ausstellen und ablegen**: der Refresh-Token wird
zurueckgegeben *und* gespeichert. Beides in einer Operation, weil ein
zurueckgegebener Refresh-Token, den niemand einloesen kann, eine Luege waere -
und weil nur die Gegenseite weiss, in welcher Transaktion sie ihn ablegt.

Ueber die Naht wandern ausschliesslich Primitive: welches Verfahren signiert
(HS256) und wie der Token abgelegt wird (als Hash), geht den Slice nichts an.
"""

from dataclasses import dataclass, field
from typing import Protocol, final

__all__ = ["IssuedSession", "RegisterUserSessionTokens"]


@final
@dataclass(frozen=True, slots=True)
class IssuedSession:
    """Die ausgestellte Sitzung - zwei Token und ihre Lebensdauern in Sekunden.

    Die Lebensdauern kommen mit heraus statt aus einer Konstanten am HTTP-Rand:
    wer den Token ausstellt, entscheidet, wie lange er gilt. Zwei Stellen mit
    derselben Zahl waeren zwei Stellen, die auseinanderlaufen koennen.
    """

    access_token: str = field(repr=False)
    expires_in: int
    refresh_token: str = field(repr=False)
    refresh_expires_in: int


class RegisterUserSessionTokens(Protocol):
    """Naht zur Sitzungsausstellung."""

    async def issue(self, user_id: str, issued_at: int) -> IssuedSession:
        """Stelle die Sitzung des Users aus und lege den Refresh-Token ab.

        `issued_at` sind Unix-Sekunden und kommen aus der Zeitquelle des Slice -
        die Gegenseite liest keine eigene Uhr, sonst haetten Nutzer-Zeile und
        Token zwei verschiedene Zeitpunkte.
        """
        ...
