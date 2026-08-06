"""HTTP-Rand des Use Case RegisterUser: `POST /api/v1/identity/register`.

Uebersetzt in beide Richtungen zwischen HTTP und den public DTOs des Slice -
camelCase nach snake_case hinein, Response-Union nach Statuscode und Body
hinaus. Es faellt hier **keine** Fachentscheidung mehr: welcher Ausgang eintritt,
steht schon fest, wenn die Pipeline zurueckkommt.
"""

from typing import final

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.api.identity.dependencies import RegisterUser
from src.api.problem_details import ProblemDetails
from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegisterUserRequest,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.shared_kernel.timestamp import Timestamp

__all__ = ["router"]

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])

_PROBLEM_JSON = "application/problem+json"


@final
class RegisterUserBody(BaseModel):
    """Der Request-Body, in der camelCase-Schreibweise der Schnittstelle."""

    model_config = ConfigDict(populate_by_name=False, extra="forbid")

    email: str
    password: str = Field(repr=False)
    display_name: str = Field(alias="displayName")
    locale: str
    time_zone_id: str = Field(alias="timeZoneId")

    def to_request(self) -> RegisterUserRequest:
        """Uebersetze in das public Request-DTO des Slice.

        Nur Umbenennung, keine Pruefung: was gueltig ist, entscheiden die Regeln
        des Slice und nicht Pydantic. Sonst laege dieselbe Fachregel an zwei
        Stellen - und die HTTP-Schicht wuerde Faelle abfangen, die die Specs des
        Slice nie zu sehen bekaemen.
        """
        return RegisterUserRequest(
            email=self.email,
            password=self.password,
            display_name=self.display_name,
            locale=self.locale,
            time_zone_id=self.time_zone_id,
        )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registriert ein neues Konto",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ProblemDetails},
        status.HTTP_409_CONFLICT: {"model": ProblemDetails},
    },
)
async def register_user(
    body: RegisterUserBody,
    pipeline: RegisterUser,
    request: Request,
) -> JSONResponse:
    """Lege ein Konto an.

    Vollstaendiges Matching ohne Auffangzweig: waechst die Response-Union um
    einen Ausgang, faellt genau hier auf, dass die HTTP-Antwort dafuer fehlt.
    """
    match await pipeline.run(body.to_request()):
        case RegistrationAccepted() as accepted:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "userId": accepted.user_id,
                    "email": accepted.email,
                    "displayName": accepted.display_name,
                    "locale": accepted.locale,
                    "timeZoneId": accepted.time_zone_id,
                    # Nach aussen ISO-8601, intern Unix-Sekunden
                    # (docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md).
                    "registeredAt": Timestamp(accepted.registered_at_unix)
                    .to_datetime()
                    .isoformat(),
                },
            )
        case EmailAlreadyTaken(email=email):
            return _problem(
                request,
                status.HTTP_409_CONFLICT,
                "email-already-registered",
                "E-Mail-Adresse bereits vergeben",
                f"Zu {email} existiert bereits ein Konto.",
            )
        case RegistrationInvalid(errors=errors):
            return _problem(
                request,
                status.HTTP_400_BAD_REQUEST,
                "validation-failed",
                "Validierung fehlgeschlagen",
                "Die Eingabe erfüllt nicht die erforderlichen Bedingungen.",
                {field: list(messages) for field, messages in errors.items()},
            )


def _problem(
    request: Request,
    http_status: int,
    error_type: str,
    title: str,
    detail: str,
    errors: dict[str, list[str]] | None = None,
) -> JSONResponse:
    """Baue eine RFC-7807-Antwort im Format des Shared Kernel."""
    problem = ProblemDetails(
        type=f"https://api.example/errors/{error_type}",
        title=title,
        status=http_status,
        detail=detail,
        instance=str(request.url.path),
        errors=errors,
    )
    return JSONResponse(
        status_code=http_status,
        content=problem.model_dump(exclude_none=True),
        media_type=_PROBLEM_JSON,
    )
