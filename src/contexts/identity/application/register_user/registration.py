"""Was am Ende der Kette steht: der aufgenommene User und seine Zugangsdaten."""

from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain import IssuedCredentials, User

__all__ = ["Registration"]


@final
@dataclass(frozen=True, slots=True)
class Registration:
    """Das Erfolgsergebnis des Use Case, bevor es zur Antwort gefaltet wird.

    Zwei Dinge statt eines, weil die Registrierung zwei erzeugt: den Nutzer und
    die Zugangsdaten, mit denen er sofort weiterarbeiten kann. Sie gehoeren
    nicht ins `User`-Aggregat - es weiss nichts von Tokens - und auch nicht erst
    an den HTTP-Rand, der sie sonst selbst ausstellen muesste.

    Der abgelegte Refresh-Token steht hier bewusst nicht: er ist ein eigenes
    Aggregat und liegt bereits in der Ablage, wenn diese Zeile entsteht. Was
    hier steht, ist nur, was der Nutzer zu sehen bekommt.

    Beide Felder sind Domaenentypen: was hier steht, hat die public Naht bereits
    hinter sich (`SessionIssuerAdapter`).
    """

    user: User
    credentials: IssuedCredentials
