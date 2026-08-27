"""Die Geltungsdauern beider Token, wie der Use Case sie nach aussen anfordert."""

from typing import Protocol

__all__ = ["RegisterUserTokenOptions"]


class RegisterUserTokenOptions(Protocol):
    """Zwei Sekundenwerte aus der Konfiguration des Prozesses.

    Kein Domain-Port: **welcher** Wert gilt, entscheidet die Umgebung. Ob er
    zulaessig ist, entscheidet `TokenLifetime`; die Fabrik (`pipeline.py`)
    wandelt an dieser Naht um. Erfuellt wird der Vertrag in der Produktion aus
    `Settings`, in Specs aus einem Fake.
    """

    @property
    def access_token_seconds(self) -> int:
        """Geltungsdauer des Access-Token."""
        ...

    @property
    def refresh_token_seconds(self) -> int:
        """Geltungsdauer des Refresh-Token."""
        ...
