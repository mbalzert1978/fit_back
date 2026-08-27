"""Feste Geltungsdauern fuer Specs - klein genug, um im Kopf nachzurechnen."""

from dataclasses import dataclass
from typing import final

__all__ = ["FixedTokenOptions"]


@final
@dataclass(frozen=True, slots=True)
class FixedTokenOptions:
    """Erfuellt `RegisterUserTokenOptions` mit erkennbar gesetzten Werten.

    Die Vorgaben sind nicht die der Produktion: ein Spec, das versehentlich an
    den echten Zahlen haengt, faellt so auf, statt stillzuhalten.
    """

    access_token_seconds: int = 60
    refresh_token_seconds: int = 3_600
