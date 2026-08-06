"""Port-Adapter des Use Case RegisterUser - der Anti-Corruption-Layer nach unten.

Hier und nur hier treffen sich die beiden Welten: die Domaene spricht Value
Objects und `Result[T, DomainError]`, die public Naht spricht Primitive und ihre
eigenen Ergebnis-Unions. Die Adapter uebersetzen in beide Richtungen und fangen
dabei nichts ab - erwartete Fehlschlaege sind bereits Ergebnistypen der Naht.
"""

from typing import final

from src.contexts.identity.application.register_user.gateway import (
    EmailFree,
    EmailTaken,
    NewUserRecord,
    RegisterUserPasswordHasher,
    RegisterUserUserStore,
    UserStored,
    WriteCollision,
)
from src.contexts.identity.domain import (
    DomainError,
    Email,
    EmailAlreadyRegistered,
    Password,
    PasswordHash,
    User,
    UserId,
    account_status_tag,
    locale_tag,
)
from src.shared_kernel import Err, Ok, Result

__all__ = ["PasswordHasherAdapter", "UserRegistryAdapter"]


@final
class UserRegistryAdapter:
    """Implementiert den Domain-Port `UserRegistry` ueber die public Naht."""

    def __init__(self, store: RegisterUserUserStore) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder Repository)."""
        self._store = store

    async def claim_email(self, email: Email) -> Result[Email, DomainError]:
        """Uebersetze die Naht-Auskunft in die Domaenen-Invariante."""
        match await self._store.find_by_email(email.value):
            case EmailTaken(user_id=user_id):
                return Err(EmailAlreadyRegistered(email, UserId.hydrate(user_id)))
            case EmailFree():
                return Ok(email)

    async def add(self, user: User) -> Result[User, DomainError]:
        """Uebersetze das Aggregat in einen flachen Datensatz und werte den Ausgang aus."""
        match await self._store.insert(_record_of(user)):
            case UserStored():
                return Ok(user)
            case WriteCollision(user_id=user_id):
                return Err(EmailAlreadyRegistered(user.email, UserId.hydrate(user_id)))


@final
class PasswordHasherAdapter:
    """Implementiert den Domain-Port `PasswordHasher` ueber die public Naht."""

    def __init__(self, hasher: RegisterUserPasswordHasher) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder Argon2id)."""
        self._hasher = hasher

    async def hash(self, password: Password) -> PasswordHash:
        """Uebersetze Value Object -> Primitiv -> Value Object."""
        return PasswordHash.hydrate(await self._hasher.hash_password(password.value))


def _record_of(user: User) -> NewUserRecord:
    """Bilde die Aggregatwurzel auf den primitiven Naht-Datensatz ab."""
    return NewUserRecord(
        user_id=str(user.id),
        email=user.email.value,
        password_hash=user.password_hash.value,
        display_name=user.display_name.value,
        locale=locale_tag(user.locale),
        time_zone_id=user.time_zone.value,
        status=account_status_tag(user.status),
        registered_at=user.registered_at,
    )
