"""Naht zum Hash-Verfahren - nicht fallibel, also ohne Ergebnis-Union."""

from typing import Protocol

__all__ = ["RegisterUserPasswordHasher"]


class RegisterUserPasswordHasher(Protocol):
    """Naht zum Passwort-Hashing.

    Kein Salt-Parameter: Argon2id erzeugt den Salt je Hash selbst und kodiert ihn
    zusammen mit den Kostenparametern in den zurueckgegebenen PHC-String
    (`$argon2id$v=19$m=...,t=...,p=...$<salt>$<hash>`). Ein Salt von aussen
    hereinzureichen waere nicht nur ueberfluessig, sondern schaedlich - es
    erlaubte dem Aufrufer, ihn wiederzuverwenden.
    """

    async def hash_password(self, plain_password: str) -> str:
        """Hashe das Klartext-Passwort und liefere den fertigen Hash-String."""
        ...
