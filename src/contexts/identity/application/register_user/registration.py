"""Was am Ende der Kette steht: der aufgenommene User und seine Sitzung."""

from dataclasses import dataclass
from typing import final

from src.contexts.identity.application.register_user.abstractions import IssuedSession
from src.contexts.identity.domain import User

__all__ = ["Registration"]


@final
@dataclass(frozen=True, slots=True)
class Registration:
    """Das Erfolgsergebnis des Use Case, bevor es zur Antwort gefaltet wird.

    Zwei Dinge statt eines, weil die Registrierung zwei erzeugt: den Nutzer und
    die Sitzung, mit der er sofort weiterarbeiten kann. Die Sitzung gehoert
    nicht ins Aggregat - `User` weiss nichts von Tokens - und auch nicht erst an
    den HTTP-Rand, der sie sonst selbst ausstellen muesste.
    """

    user: User
    session: IssuedSession
