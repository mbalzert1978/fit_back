"""Erfuellt die Naht `RegisterUserPasswordHasher` ueber Argon2id.

Kennt die Domaene nicht: String hinein, PHC-String heraus. Den Domain-Port
`PasswordHasher` implementiert `application/register_user/adapters/`.
"""

import asyncio
from typing import final

from argon2 import PasswordHasher as Argon2

__all__ = ["Argon2PasswordHasher"]


@final
class Argon2PasswordHasher:
    """Hasht Passwoerter mit Argon2id in den Standard-Parametern der Bibliothek.

    Die Kostenparameter kommen bewusst aus `argon2-cffi` und werden hier nicht
    ueberschrieben: sie folgen den aktuellen OWASP-Empfehlungen und werden mit
    der Bibliothek gepflegt. Eigene Werte waeren eine Momentaufnahme, die
    niemand mehr nachzieht - und sie stehen ohnehin in jedem erzeugten Hash, ein
    spaeterer Wechsel ist daher beim naechsten Login erkennbar und nachholbar.
    """

    def __init__(self) -> None:
        """Baue den Hasher mit den Standardparametern der Bibliothek."""
        self._argon2 = Argon2()

    async def hash_password(self, plain_password: str) -> str:
        """Hashe das Passwort und gib den vollstaendigen PHC-String zurueck.

        Ausgelagert in einen Thread: Argon2id ist absichtlich rechen- und
        speicherintensiv und blockiert im Event-Loop sonst jede andere Anfrage
        fuer die Dauer des Hashens (.rules/python/python-async.md, "No Blocking").
        """
        return await asyncio.to_thread(self._argon2.hash, plain_password)
