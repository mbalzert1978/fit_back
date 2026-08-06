"""Implementiert den Domain-Port `UserRegistry` ueber die public Naht."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    EmailTaken,
    NewUserRecord,
    RegisterUserUserStore,
    UserStored,
)
from src.contexts.identity.domain import (
    DomainError,
    EmailAlreadyRegistered,
    User,
    account_status_tag,
    locale_tag,
)
from src.contexts.shared_kernel import Err, Ok, Result

__all__ = ["UserRegistryAdapter"]


@final
class UserRegistryAdapter:
    """Uebersetzt Aggregat -> Datensatz und Naht-Union -> Domaenen-`Result`."""

    def __init__(self, store: RegisterUserUserStore) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder Repository)."""
        self._store = store

    async def add(self, user: User) -> Result[User, DomainError]:
        """Nimm den User auf und werte das Urteil des Bestands aus."""
        match await self._store.insert(_record_of(user)):
            case UserStored():
                return Ok(user)
            case EmailTaken():
                return Err(EmailAlreadyRegistered(user.email))


def _record_of(user: User) -> NewUserRecord:
    """Bilde die Aggregatwurzel auf den primitiven Naht-Datensatz ab."""
    return NewUserRecord(
        user_id=str(user.id),
        email=user.email.value,
        password_hash=user.password_hash.value,
        display_name=user.display_name.text,
        locale=locale_tag(user.locale),
        time_zone_id=user.time_zone.value,
        status=account_status_tag(user.status),
        registered_at=user.registered_at.unix_seconds,
    )
