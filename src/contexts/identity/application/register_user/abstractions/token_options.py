"""Die Geltungsdauern beider Token, wie der Use Case sie nach aussen anfordert."""

from typing import Protocol

__all__ = ["RegisterUserTokenOptions"]


class RegisterUserTokenOptions(Protocol):
    """Zwei Sekundenwerte aus der Konfiguration des Prozesses.

    Kein Domain-Port: die Domaene entscheidet nicht, wie lange ein Zugang gilt,
    sie bekommt die Zahl als Primitiv gereicht. Erfuellt wird der Vertrag in der
    Produktion aus `Settings`, in Specs aus einem Fake.
    """

    @property
    def access_token_seconds(self) -> int:
        """Geltungsdauer des Access-Token."""
        ...

    @property
    def refresh_token_seconds(self) -> int:
        """Geltungsdauer des Refresh-Token."""
        ...
