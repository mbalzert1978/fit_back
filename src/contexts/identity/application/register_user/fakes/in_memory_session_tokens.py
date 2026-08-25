"""In-Memory-Sitzungsausstellung: deterministisch, ohne Signaturverfahren."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import IssuedSession

__all__ = ["ACCESS_TOKEN_LIFETIME", "REFRESH_TOKEN_LIFETIME", "InMemorySessionTokens"]

ACCESS_TOKEN_LIFETIME = 900
REFRESH_TOKEN_LIFETIME = 5_184_000
"""Dieselben Lebensdauern wie in der Produktion (BACKEND.md Abschnitt 8).

Abgeschrieben und nicht importiert: die Produktionswerte stehen in der
Infrastruktur, und die Fakes sind Teil des Slice - er darf sie nicht kennen.
Ein Spec, der eine Lebensdauer prueft, prueft damit die des Fakes; die der
Produktion prueft der Vertragslauf.
"""


@final
class InMemorySessionTokens:
    """Erfuellt `RegisterUserSessionTokens` fuer Specs.

    Merkt sich, was sie ausgestellt hat - der abgelegte Refresh-Token ist in der
    Produktion eine Datenbankzeile, hier eine Liste, und in beiden Faellen
    nachprueftbar.
    """

    def __init__(self) -> None:
        """Starte ohne ausgestellte Sitzung."""
        self.issued: list[tuple[str, str]] = []
        """Je Ausstellung `(user_id, refresh_token)` - in der Reihenfolge des Ausstellens."""

    async def issue(self, user_id: str, issued_at: int) -> IssuedSession:
        """Stelle eine erkennbar unechte Sitzung aus und lege sie ab."""
        refresh_token = f"fake-refresh-{user_id}-{issued_at}"
        self.issued.append((user_id, refresh_token))
        return IssuedSession(
            access_token=f"fake-access-{user_id}-{issued_at}",
            expires_in=ACCESS_TOKEN_LIFETIME,
            refresh_token=refresh_token,
            refresh_expires_in=REFRESH_TOKEN_LIFETIME,
        )
