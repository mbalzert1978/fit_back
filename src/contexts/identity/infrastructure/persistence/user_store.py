"""Erfuellt die Naht `RegisterUserUserStore` ueber `identity.users`.

Implementiert **nicht** den Domain-Port `UserRegistry` - das tut
`application/register_user/adapters/user_registry_adapter.py`. Dieses Modul kennt
die Domaene nicht: Primitive hinein, die Ergebnis-Union der Naht heraus.
"""

from typing import Protocol, final

from sqlalchemy import Result, TextClause, text

from src.contexts.identity.application.register_user.abstractions import (
    EmailTaken,
    NewUserRecord,
    UserInsertion,
    UserStored,
)

__all__ = ["PostgresUserStore", "UserStoreTransaction"]


class UserStoreTransaction(Protocol):
    """Der Ausfuehrungskanal in der laufenden Transaktion des Vorgangs.

    Genau eine Methode, kein `commit`: der Nutzer-Datensatz und das
    `UserRegistered`-Ereignis in der Outbox muessen gemeinsam sichtbar werden
    oder gar nicht. Wer hier committen koennte, koennte die beiden trennen.
    """

    async def execute(self, statement: TextClause, parameters: object = None, /) -> Result[object]:
        """Fuehre ein Statement in der laufenden Transaktion aus."""
        ...


# `ON CONFLICT DO NOTHING RETURNING id`: ein einziges Statement entscheidet die
# Eindeutigkeit und meldet sie zurueck. Kein vorheriges SELECT (das waere im
# Moment seiner Beantwortung schon veraltet) und kein abgefangener
# IntegrityError - eine verletzte Constraint bricht die Transaktion in Postgres
# ab, sodass danach nicht einmal mehr eine Nachfrage moeglich waere.
_INSERT_USER: TextClause = text("""
    INSERT INTO identity.users (
        id, email, password_hash, display_name, locale, time_zone_id, status, registered_at
    )
    VALUES (
        :user_id, :email, :password_hash, :display_name, :locale, :time_zone_id,
        :status, :registered_at
    )
    ON CONFLICT (email) DO NOTHING
    RETURNING id
""")


@final
class PostgresUserStore:
    """Schreibt neue Nutzer nach `identity.users`."""

    def __init__(self, transaction: UserStoreTransaction) -> None:
        """Nimm die laufende Transaktion des Vorgangs entgegen."""
        self._transaction = transaction

    async def insert(self, record: NewUserRecord) -> UserInsertion:
        """Schreibe den Datensatz; melde eine bereits vergebene E-Mail."""
        written = await self._transaction.execute(
            _INSERT_USER,
            {
                "user_id": record.user_id,
                "email": record.email,
                "password_hash": record.password_hash,
                "display_name": record.display_name,
                "locale": record.locale,
                "time_zone_id": record.time_zone_id,
                "status": record.status,
                "registered_at": record.registered_at,
            },
        )
        # Keine zurueckgegebene Zeile heisst: der Constraint hat den Einfuegen
        # verhindert, die Adresse ist vergeben.
        return UserStored() if written.first() is not None else EmailTaken()
