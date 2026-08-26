"""Die Fehlerformen des Frontend-Vertrags von `POST /api/v1/identity/register`.

Hier steht **nur**, wie ein abgelehnter Versuch als HTTP-Antwort aussieht: welcher
Statuscode, welcher Fehler-Slug, und wie aus den Fehlercodes des Slice Text in der
ausgehandelten Sprache wird.

Getrennt vom Router aus demselben Grund wie `register_user_response.py` nebenan:
beide aendern sich aus verschiedenen Gruenden. Die Fehlerform, wenn das Frontend
einen anderen Fehlerkoerper braucht; der Router, wenn sich Pfad, Statuscodes oder
Verdrahtung aendern. Der Router entschied das vorher selbst und trug damit drei
Aufgaben statt einer.

Der `match` ist flach ueber `RegisterUserFailure` und schliesst mit `assert_never` -
dasselbe Muster wie `to_response` im Slice
(`.rules/python/python-error-handling.md`, "Jeder `match` ist vollstaendig").
"""

from collections.abc import Callable, Mapping
from functools import partial
from typing import Annotated, assert_never

from fastapi import Depends, Request, status

from src.api.i18n import language_of, resources_of, translate
from src.api.problem_details import ProblemResponse, translated_problem
from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegisterUserFailure,
    RegistrationInvalid,
)
from src.contexts.shared_kernel.validation import FieldErrorDetail

__all__ = ["Problems", "to_problem"]


def _problems(request: Request) -> Callable[[RegisterUserFailure], ProblemResponse]:
    """Binde `to_problem` an die laufende Anfrage.

    Damit steht die Anfrage nicht mehr in der Signatur des Endpunkts. Er
    beantwortet eine Ablehnung, ohne zu wissen, dass dafuer Pfad und
    `Accept-Language` der Anfrage gebraucht werden - beides steckt hier drin.

    Ein `partial` und keine Klasse: gebunden wird genau ein Argument, und
    `to_problem` bleibt die gewoehnliche Funktion, die sich ohne FastAPI
    aufrufen laesst.
    """
    return partial(to_problem, request)


type Problems = Annotated[Callable[[RegisterUserFailure], ProblemResponse], Depends(_problems)]
"""Die Fehlerformen dieses Endpunkts, fertig an die Anfrage gebunden."""


def to_problem(request: Request, rejected: RegisterUserFailure) -> ProblemResponse:
    """Beantworte einen abgelehnten Registrierungsversuch als `problem+json`.

    Waechst die Fehlerhaelfte der Pipeline um einen Ausgang, faellt genau hier
    auf, dass die HTTP-Antwort dafuer fehlt - `RegisterUserFailure` ist
    geschlossen, und `assert_never` schliesst den `match`.
    """
    match rejected:
        case EmailAlreadyTaken(email=email):
            return translated_problem(
                request,
                status.HTTP_409_CONFLICT,
                "email-already-registered",
                parameters={"email": email},
            )

        case RegistrationInvalid(errors=errors):
            return translated_problem(
                request,
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "validation-failed",
                errors=_rendered(request, errors),
            )

        case _:
            assert_never(rejected)


def _rendered(
    request: Request, errors: Mapping[str, tuple[FieldErrorDetail, ...]]
) -> dict[str, list[str]]:
    """Uebersetze die Fehlercodes je Feld in Saetze der ausgehandelten Sprache.

    Ueber die Naht des Use Case kommen Code und Parameter, nie ein fertiger Satz
    (`.rules/python/python-feature-slices.md`). Der Satz entsteht erst hier, weil
    erst hier bekannt ist, in welcher Sprache der Aufrufer ihn lesen will.
    """
    resources = resources_of(request)
    language = language_of(request)
    return {
        field: [translate(resources, code, parameters, language) for code, parameters in faults]
        for field, faults in errors.items()
    }
