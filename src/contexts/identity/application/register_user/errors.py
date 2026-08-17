"""Der **eine** Fehlerkanal des Use Case RegisterUser.

Bis Stufe 3 hatte der Slice zwei: `list[FieldError]` aus der Validierung und den
Domaenenfehler aus dem Handler, verbunden durch ein `if` und gefaltet in
**zwei** Aufrufe derselben Response-Union. Ein gemeinsamer Fehlertyp laesst
beide zusammenfallen - danach gibt es eine Kette und genau einen Fold.

Die Union ist bewusst ausgeschrieben (`RequestInvalid | EmailAlreadyRegistered`)
und nicht ueber `UserRegistryError` gebildet: waechst die Port-Union, soll das
eine Aenderung **hier** erzwingen und nicht still durchschlagen. Der Fold in
`mappers/register_user_response_mapper.py` haette den neuen Fall sonst erst zur
Laufzeit im `assert_never` gemeldet.
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
