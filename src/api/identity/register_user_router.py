"""HTTP-Rand des Use Case RegisterUser: `POST /api/v1/identity/register`.

Übersetzt in beide Richtungen zwischen HTTP und den public DTOs des Slice:
- camelCase nach snake_case hinein
- Response-Union nach Statuscode und Body hinaus
- Error-Codes nach Accept-Language zu Texten

Es fällt hier **keine** Fachentscheidung mehr: welcher Ausgang eintritt, steht
schon fest, wenn die Pipeline zurückkommt. Die Sprachauswahl ist rein
präsentativ und beeinflußt das fachliche Ergebnis nicht.
"""

from typing import Literal, assert_never, final

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.api.i18n import ResourcesCache, get_language_from_header, translate
from src.api.identity.dependencies import RegisterUser
from src.api.problem_details import ProblemDetails, translated_problem
from src.contexts.identity.application.register_user import (
    EmailAlreadyTaken,
    RegisterUserRequest,
    RegistrationAccepted,
    RegistrationInvalid,
)

__all__ = ["router"]

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])

type TokenType = Literal["Bearer"]
"""Das Schema, in dem der Access-Token vorzulegen ist (RFC 6750).

Steht ohne Matcher im Vertrag und ist damit bindend - ein Typ mit genau einem
bewohnbaren Wert und kein Wert, den irgendwer waehlen koennte. Als Typ und
nicht als Konstante, weil `Literal[...]` nur echte Literale annimmt: ein Name
darin ist zur Laufzeit unauffaellig und statisch ungueltig.

Das Feld traegt bewusst **keinen** Default: ein Default nimmt es aus `required`
des Schemas, und dann behauptet die Dokumentation, ein bindendes Feld duerfe
fehlen. Der Wert wird an der Aufrufstelle gesetzt.
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


@final
class RegisteredUser(BaseModel):
    """Das angelegte Konto, in der camelCase-Schreibweise der Schnittstelle."""

    id: str
    email: str
    display_name: str = Field(serialization_alias="displayName")
    locale: str
    time_zone_id: str = Field(serialization_alias="timeZoneId")


@final
class GrantedSession(BaseModel):
    """Die mit der Registrierung ausgegebene Sitzung."""

    access_token: str = Field(serialization_alias="accessToken", repr=False)
    expires_in: int = Field(serialization_alias="expiresIn")
    refresh_token: str = Field(serialization_alias="refreshToken", repr=False)
    refresh_expires_in: int = Field(serialization_alias="refreshExpiresIn")
    token_type: TokenType = Field(serialization_alias="tokenType")


@final
class RegisterUserResponse(BaseModel):
    """Der 201-Koerper: der nackte `data`-Teil, ohne den Umschlag der Middleware."""

    user: RegisteredUser
    session: GrantedSession


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
    # Wähle Sprache nach Accept-Language
    language = get_language_from_header(request.headers.get("accept-language"))
    resources: ResourcesCache = request.app.state.resources

    outcome = await pipeline.run(body.to_request())
    match outcome:
        case RegistrationAccepted() as accepted:
            # Der `{data, meta}`-Umschlag kommt aus `ResponseEnvelopeMiddleware`,
            # ebenso `X-Request-Id` und `Cache-Control`. Hier steht nur, was
            # dieser Endpunkt zu sagen hat.
            response.headers["Content-Language"] = language
            response.headers["Location"] = _SELF_URL
            return RegisterUserResponse(
                user=RegisteredUser(
                    id=accepted.user_id,
                    email=accepted.email,
                    display_name=accepted.display_name,
                    locale=accepted.locale,
                    time_zone_id=accepted.time_zone_id,
                ),
                session=GrantedSession(
                    access_token=accepted.access_token,
                    expires_in=accepted.expires_in,
                    refresh_token=accepted.refresh_token,
                    refresh_expires_in=accepted.refresh_expires_in,
                    token_type="Bearer",  # noqa: S106 -- Schema-Name aus RFC 6750, kein Geheimnis
                ),
            )

        case EmailAlreadyTaken(email=email):
            return translated_problem(
                request,
                status.HTTP_409_CONFLICT,
                "email-already-registered",
                resources,
                language=language,
                parameters={"email": email},
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

            return translated_problem(
                request,
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "validation-failed",
                resources,
                language=language,
                errors=translated_errors,
            )

        case _:
            assert_never(outcome)
