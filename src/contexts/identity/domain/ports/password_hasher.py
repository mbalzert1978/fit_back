"""Domain-Port PasswordHasher - das Verfahren selbst (Argon2id) lebt ausserhalb."""

from typing import Protocol

from src.contexts.identity.domain.value_objects.password import Password
from src.contexts.identity.domain.value_objects.password_hash import PasswordHash

__all__ = ["PasswordHasher"]


class PasswordHasher(Protocol):
    """Verwandelt ein geprueftes Klartext-Passwort in seinen Hash.

    Bewusst **nicht** fallibel deklariert: ein fehlschlagender Hash ist ein Bug
    (falsche Konfiguration), kein erwarteter Fachfall - also wird nichts gefangen
    und nichts als `Result` maskiert (.rules/python/python-error-handling.md).
    """

    async def hash(self, password: Password) -> PasswordHash:
        """Hashe das Klartext-Passwort."""
        ...
