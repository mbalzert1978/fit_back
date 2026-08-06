"""In-Memory-Hasher: deterministisch, nicht umkehrbar, ohne Argon2-Abhaengigkeit."""

from hashlib import sha256
from typing import final

__all__ = ["DeterministicPasswordHasher"]

_PREFIX = "fake-argon2id$"


@final
class DeterministicPasswordHasher:
    """Erfuellt `RegisterUserPasswordHasher` fuer Specs.

    Deterministisch, damit Specs reproduzierbar sind, und nicht umkehrbar, damit
    ein Fake-Hash in einem Testlog kein Klartext-Passwort preisgibt. Das echte
    Argon2id-Verfahren kommt in Stufe 2 hinter dieselbe Naht.
    """

    async def hash_password(self, plain_password: str) -> str:
        """Hashe deterministisch ueber SHA-256 mit erkennbarem Fake-Praefix."""
        return _PREFIX + sha256(plain_password.encode()).hexdigest()
