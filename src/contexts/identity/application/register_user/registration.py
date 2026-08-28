"""Was am Ende der Kette steht: der aufgenommene User und seine Zugangsdaten."""

from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain import IssuedCredentials, User

__all__ = ["Registration"]


@final
@dataclass(frozen=True, slots=True)
class Registration:
    """Das Erfolgsergebnis des Use Case, bevor es zur Antwort gefaltet wird.

    Nur, was der Nutzer zu sehen bekommt: der abgelegte Refresh-Token ist ein
    eigenes Aggregat und steht hier nicht
    (docs/decisions/2026-08-27-1830-refresh-token-ist-ein-aggregat.md).
    """

    user: User
    credentials: IssuedCredentials
