"""HTTP-Rand des Use Case RegisterUser: `POST /api/v1/identity/register`.

Hier stehen Routing und Verdrahtung: welcher Pfad, welche Statuscodes, welche
Dependency - und welcher Ausgang der Pipeline zu welcher der beiden
Antwortformen fuehrt.

Es faellt hier **keine** Fachentscheidung mehr: welcher Ausgang eintritt, steht
schon fest, wenn die Pipeline zurueckkommt.

Wie Anfrage und Antworten aussehen, steht nebenan und nicht hier:

- `register_user_body.py` — der Anfrage-Rumpf
- `register_user_response.py` — der 201-Koerper samt seiner Kopfzeilen
- `register_user_problem.py` — die 409- und 422-Koerper samt ihrer Uebersetzung
"""

from typing import assert_never

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from src.api.identity.dependencies import RegisterUser
from src.api.identity.register_user_body import RegisterUserBody
from src.api.identity.register_user_problem import to_problem
from src.api.identity.register_user_response import RegisterUserResponse, apply_created_headers
from src.api.problem_details import ProblemDetails
from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegistrationAccepted,
    RegistrationInvalid,
)

__all__ = ["router"]

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registriert ein neues Konto",
    response_model=RegisterUserResponse,
    responses={
        status.HTTP_409_CONFLICT: {"model": ProblemDetails},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ProblemDetails},
    },
)
async def register_user(
    body: RegisterUserBody,
    pipeline: RegisterUser,
    request: Request,
    response: Response,
) -> RegisterUserResponse | JSONResponse:
    """Lege ein Konto an.

    Vollstaendiges Matching mit `assert_never` als Abschluss: waechst die
    Response-Union um einen Ausgang, faellt genau hier auf, dass die HTTP-Antwort
    dafuer fehlt. Ohne diesen Zweig faellt der `match` still durch und die Funktion
    liefert `None` - Python erzwingt Vollzaehligkeit zur Laufzeit nicht
    (.rules/python/python-error-handling.md, "Jeder `match` ist vollstaendig").
    """
    outcome = await pipeline.run(body.to_request())
    match outcome:
        case RegistrationAccepted() as accepted:
            apply_created_headers(response, request)
            return RegisterUserResponse.to_response(accepted)

        case EmailAlreadyTaken() | RegistrationInvalid() as rejected:
            return to_problem(request, rejected)

        case _:
            assert_never(outcome)
