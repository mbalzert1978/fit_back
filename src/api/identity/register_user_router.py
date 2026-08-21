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
from src.api.problem_details import ProblemDetails, problem_type
from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegisterUserRequest,
    RegistrationAccepted,
    RegistrationInvalid,
)

__all__ = ["router"]

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])

_PROBLEM_JSON = "application/problem+json"

_TOKEN_TYPE = "Bearer"  # noqa: S105 -- ein Schema-Name aus RFC 6750, kein Geheimnis
"""Das Schema, in dem der Access-Token vorzulegen ist (RFC 6750).

Steht ohne Matcher im Vertrag und ist damit bindend - eine Konstante und kein
Wert, den irgendwer waehlen koennte.
"""

_SELF_URL = "/api/v1/identity/me"
"""Wohin die 201 zeigt: auf das angelegte Konto.

Der Endpunkt selbst entsteht mit #55; der Header zeigt schon dorthin, weil er
Teil des Vertrags dieser Antwort ist und nicht Teil jenes Endpunkts.
"""


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
        status.HTTP_409_CONFLICT: {"model": ProblemDetails},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ProblemDetails},
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
            # Der `{data, meta}`-Umschlag kommt aus `ResponseEnvelopeMiddleware`,
            # ebenso `X-Request-Id` und `Cache-Control`. Hier steht nur, was
            # dieser Endpunkt zu sagen hat.
            response = JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "user": {
                        "id": accepted.user_id,
                        "email": accepted.email,
                        "displayName": accepted.display_name,
                        "locale": accepted.locale,
                        "timeZoneId": accepted.time_zone_id,
                    },
                    "session": {
                        "accessToken": accepted.access_token,
                        "expiresIn": accepted.expires_in,
                        "refreshToken": accepted.refresh_token,
                        "refreshExpiresIn": accepted.refresh_expires_in,
                        "tokenType": _TOKEN_TYPE,
                    },
                },
            )
            response.headers["Content-Language"] = language
            response.headers["Location"] = _SELF_URL
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
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "validation-failed",
                title,
                detail,
                translated_errors,
                language_tag=language,
            )

        case _:
            assert_never(outcome)


def _problem(  # noqa: PLR0913, PLR0917 -- API response builder needs context, status, type, and text
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
        type=problem_type(error_type),
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
