"""Das Konto, das die Provider-States des Identity-Vertrags beschreiben.

Geseedet wird ueber die vorhandene `postgres_engine`-Fixture und direkt gegen
`identity.users` - **nicht** ueber den Endpunkt, den die Verifikation gerade
prueft: ein State, der sich auf sein eigenes Pruefobjekt stuetzt, belegt nichts.
"""

from typing import final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.contexts.identity.infrastructure.hashing import Argon2PasswordHasher

__all__ = ["Testkonto"]

_ANLEGEN = text(
    "INSERT INTO identity.users ("
    " id, email, password_hash, display_name, locale, time_zone_id, status, registered_at"
    ") VALUES ("
    " :user_id, :email, :password_hash, 'Anna', 'de', 'Europe/Berlin', 'active', :registered_at"
    ")"
)
_ENTFERNEN = text("DELETE FROM identity.users WHERE email = :email")

_USER_ID = "01920000-0000-7000-8000-000000000094"
_REGISTRIERT_AM = 1_700_000_000
"""Unix-**Sekunden**, wie ueberall in diesem Repo
(`docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md`). Fest gewaehlt:
keine der fuenf Interaktionen liest den Wert.
"""


@final
class Testkonto:
    """Legt genau ein Konto an und raeumt es wieder weg."""

    __test__ = False  # Hilfsmittel, kein Testfall - sonst versucht pytest, es einzusammeln

    def __init__(self, engine: AsyncEngine, *, email: str, passwort: str) -> None:
        """Nimm die Engine des Tests und die Daten aus dem State-Namen entgegen."""
        self._engine = engine
        self._email = email
        self._passwort = passwort

    async def anlegen(self) -> None:
        """Lege das Konto an.

        Raeumt bewusst **nicht** vorher auf: eine belegte Adresse laesst den
        `uq_users_email` zuschlagen, und genau das soll sie. Ein Setup, das sich
        selbst freiraeumt, verschweigt einen ausgefallenen Teardown - und mit ihm
        den Fall, in dem zwei Interaktionen desselben States einander stoeren.
        """
        passwort_hash = await Argon2PasswordHasher().hash_password(self._passwort)
        async with self._engine.begin() as verbindung:
            await verbindung.execute(
                _ANLEGEN,
                {
                    "user_id": _USER_ID,
                    "email": self._email,
                    "password_hash": passwort_hash,
                    "registered_at": _REGISTRIERT_AM,
                },
            )

    async def entfernen(self) -> None:
        """Gib die Adresse wieder frei, egal wer sie belegt hat."""
        async with self._engine.begin() as verbindung:
            await verbindung.execute(_ENTFERNEN, {"email": self._email})
