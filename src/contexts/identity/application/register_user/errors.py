"""Der eine Fehlerkanal des Use Case RegisterUser.

Die Union ist ausgeschrieben (`RequestInvalid | EmailAlreadyRegistered`) und nicht ueber
`UserRegistryError` gebildet: waechst die Port-Union, soll das eine Aenderung hier
erzwingen. Gemessen wird das von
`tests/contexts/identity/test_register_user_error_channel.py`.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain import EmailAlreadyRegistered
from src.contexts.shared_kernel.validation import FieldError

__all__ = ["RegisterUserError", "RequestInvalid", "request_invalid"]


@final
@dataclass(frozen=True, slots=True)
class RequestInvalid:
    """Die Eingabe hat das Regelwerk nicht bestanden - mit allen Befunden auf einmal.

    Traegt die gesammelten `FieldError` weiter, nicht deren Formulierung: Feld,
    Code und Parameter sind sprachunabhaengig, der Text entsteht erst am
    HTTP-Rand nach `Accept-Language`.
    """

    errors: tuple[FieldError, ...]


def request_invalid(errors: Sequence[FieldError]) -> RequestInvalid:
    """Hebe die gesammelten Feldfehler in den Fehlerkanal der Pipeline."""
    return RequestInvalid(tuple(errors))


type RegisterUserError = RequestInvalid | EmailAlreadyRegistered
