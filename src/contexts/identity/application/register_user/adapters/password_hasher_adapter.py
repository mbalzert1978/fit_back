"""Implementiert den Domain-Port `PasswordHasher` ueber die public Naht."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    RegisterUserPasswordHasher,
)
from src.contexts.identity.domain import Password, PasswordHash

__all__ = ["PasswordHasherAdapter"]


@final
class PasswordHasherAdapter:
    """Uebersetzt Value Object -> Primitiv -> Value Object."""

    def __init__(self, hasher: RegisterUserPasswordHasher) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder Argon2id)."""
        self._hasher = hasher

    async def hash(self, password: Password) -> PasswordHash:
        """Hashe das Klartext-Passwort."""
        return PasswordHash.hydrate(await self._hasher.hash_password(password.value))
