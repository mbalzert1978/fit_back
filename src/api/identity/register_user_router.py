"""HTTP-Rand des Use Case RegisterUser: `POST /api/v1/identity/register`.

Übersetzt in beide Richtungen zwischen HTTP und den public DTOs des Slice:
- camelCase nach snake_case hinein
- Response-Union nach Statuscode und Body hinaus
- Error-Codes nach Accept-Language zu Texten

Es fällt hier **keine** Fachentscheidung mehr: welcher Ausgang eintritt, steht
schon fest, wenn die Pipeline zurückkommt. Die Sprachauswahl ist rein
präsentativ und beeinflußt das fachliche Ergebnis nicht.
"""

from typing import assert_never, final

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.api.i18n import ResourcesCache, get_language_from_header, translate
from src.api.identity.dependencies import RegisterUser
from src.api.problem_details import ProblemDetails
from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegisterUserRequest,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.shared_kernel.timestamp import Timestamp

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

    Vollstaendiges Matching mit `assert_never` als Abschluss: waechst die
    Response-Union um einen Ausgang, faellt genau hier auf, dass die HTTP-Antwort
    dafuer fehlt. Ohne diesen Zweig faellt der `match` still durch und die Funktion
    liefert `None` - Python erzwingt Vollzaehligkeit zur Laufzeit nicht
    (.rules/python/python-error-handling.md, "Jeder `match` ist vollstaendig").
    """
    # Wähle Sprache nach Accept-Language
    language = get_language_from_header(request.headers.get("accept-language"))
    resources: ResourcesCache = request.app.state.resources

    outcome = await pipeline.run(body.to_request())
    match outcome:
        case RegistrationAccepted() as accepted:
            response = JSONResponse(
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
            response.headers["Content-Language"] = language
            return response

        case EmailAlreadyTaken(email=email):
            title = translate(resources, "email-already-registered", language=language)
            detail = translate(
                resources, "email-already-registered-detail", {"email": email}, language
            )
            return _problem(
                request,
                status.HTTP_409_CONFLICT,
                "email-already-registered",
                title,
                detail,
                language_tag=language,
            )

        case RegistrationInvalid(errors=errors):
            # Übersetze error codes zu Texten
            # errors: Mapping[str, tuple[FieldErrorDetail, ...]]
            # FieldErrorDetail = tuple[str, Mapping[str, object]]
            translated_errors: dict[str, list[str]] = {}
            for field, field_errors in errors.items():
                messages: list[str] = []
                for code, parameters in field_errors:
                    text = translate(resources, code, parameters, language)
                    messages.append(text)
                translated_errors[field] = messages

            title = translate(resources, "validation-failed", language=language)
            detail = translate(resources, "validation-failed-detail", language=language)
            return _problem(
                request,
                status.HTTP_400_BAD_REQUEST,
                "validation-failed",
                title,
                detail,
                translated_errors,
                language_tag=language,
            )

        case _:
            assert_never(outcome)


def _problem(
    request: Request,
    http_status: int,
    error_type: str,
    title: str,
    detail: str,
    errors: dict[str, list[str]] | None = None,
    language_tag: str = "de-DE",
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
    response = JSONResponse(
        status_code=http_status,
        content=problem.model_dump(exclude_none=True),
        media_type=_PROBLEM_JSON,
    )
    response.headers["Content-Language"] = language_tag
    return response
