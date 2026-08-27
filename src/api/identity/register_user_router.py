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

from typing import Final, assert_never

from fastapi import APIRouter, status

from src.api.identity.dependencies import RegisterUser
from src.api.identity.register_user_body import RegisterUserBody
from src.api.identity.register_user_problem import Problems
from src.api.identity.register_user_response import CreatedHeaders, RegisterUserResponse
from src.api.problem_details import ProblemDetails, ProblemResponse
from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegistrationAccepted,
    RegistrationInvalid,
)

__all__ = ["router"]

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])

_CREATED_HEADERS: Final = {
    "Location": {
        "description": "Das angelegte Konto.",
        "schema": {"type": "string", "format": "uri-reference"},
    },
    "Content-Language": {
        "description": "Die Sprache, in der dieser Koerper beantwortet wurde.",
        "schema": {"type": "string"},
    },
}
"""Die Kopfzeilen, die nur zur 201 **dieser** Route gehoeren.

Hier und nicht im Nachtrag an der Beschreibung (`src/api/openapi.py`): der
setzt ein, was fuer jede Antwort des Hosts gilt. Diese zwei setzt
`apply_created_headers` und sonst niemand.
"""


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registriert ein neues Konto",
    response_model=RegisterUserResponse,
    responses={
        status.HTTP_201_CREATED: {"headers": _CREATED_HEADERS},
        status.HTTP_409_CONFLICT: {"model": ProblemDetails},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ProblemDetails},
    },
)
async def register_user(
    body: RegisterUserBody,
    pipeline: RegisterUser,
    created: CreatedHeaders,
    problems: Problems,
) -> RegisterUserResponse | ProblemResponse:
    """Lege ein Konto an.

    Weder `Request` noch `Response` stehen in der Signatur. Beide werden hier
    gebraucht - fuer `instance` des Fehlerkoerpers, fuer die ausgehandelte
    Sprache, fuer `Location` -, aber keine dieser Verwendungen ist eine
    Entscheidung dieses Endpunkts. Sie stecken in `created` und `problems`, zwei
    Dependencies, die bereits an die laufende Anfrage gebunden sind.

    Kein `JSONResponse` als Rueckgabetyp - das sagte nur "JSON" und liesse
    jeden beliebigen Koerper zu.

    Vollstaendiges Matching mit `assert_never` als Abschluss: waechst die
    Response-Union um einen Ausgang, faellt genau hier auf, dass die HTTP-Antwort
    dafuer fehlt. Ohne diesen Zweig faellt der `match` still durch und die Funktion
    liefert `None` - Python erzwingt Vollzaehligkeit zur Laufzeit nicht
    (.rules/python/python-error-handling.md, "Jeder `match` ist vollstaendig").
    """
    outcome = await pipeline.run(body.to_request())
    match outcome:
        case RegistrationAccepted() as accepted:
            created()
            return RegisterUserResponse.to_response(accepted)

        case EmailAlreadyTaken() | RegistrationInvalid() as rejected:
            return problems(rejected)

        case _:
            assert_never(outcome)
