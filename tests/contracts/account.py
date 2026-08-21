"""The account the identity pact's provider states describe.

Seeded via the existing `postgres_engine` fixture, straight against
`identity.users` - **not** via the endpoint the verification is currently
checking: a state that leans on its own subject under test proves nothing.
"""

from typing import final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.contexts.identity.infrastructure.hashing import Argon2PasswordHasher

__all__ = ["Account"]

_INSERT = text(
    "INSERT INTO identity.users ("
    " id, email, password_hash, display_name, locale, time_zone_id, status, registered_at"
    ") VALUES ("
    " :user_id, :email, :password_hash, 'Anna', 'de', 'Europe/Berlin', 'active', :registered_at"
    ")"
)
_DELETE = text("DELETE FROM identity.users WHERE email = :email")

_USER_ID = "01920000-0000-7000-8000-000000000094"
_REGISTERED_AT = 1_700_000_000
"""Unix **seconds**, as everywhere in this repo
(`docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md`). Fixed
arbitrarily: none of the five interactions reads the value.
"""


@final
class Account:
    """Creates exactly one account and cleans it back up."""

    def __init__(self, engine: AsyncEngine, *, email: str, password: str) -> None:
        self._engine = engine
        self._email = email
        self._password = password

    async def create(self) -> None:
        """Deliberately does **not** clean up first: a taken address is meant to
        hit `uq_users_email`. A setup that clears its own way would hide a
        failed teardown - and with it the case where two interactions of the
        same state interfere with each other.
        """
        password_hash = await Argon2PasswordHasher().hash_password(self._password)
        async with self._engine.begin() as connection:
            await connection.execute(
                _INSERT,
                {
                    "user_id": _USER_ID,
                    "email": self._email,
                    "password_hash": password_hash,
                    "registered_at": _REGISTERED_AT,
                },
            )

    async def remove(self) -> None:
        """Free the address again, no matter who holds it."""
        async with self._engine.begin() as connection:
            await connection.execute(_DELETE, {"email": self._email})
