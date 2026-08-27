"""Die Antwortform des Frontend-Vertrags von `POST /api/v1/identity/register`.

Hier steht **nur**, wie die 201 aussieht: die drei Modelle des `data`-Teils, das
Token-Schema, das eines ihrer Felder bindet, und die beiden Kopfzeilen, die zu
dieser Antwort gehoeren. Kein Routing, keine Dependencies, keine
Fachentscheidung.

Getrennt vom Router, weil beide sich aus verschiedenen Gruenden aendern: die
Vertragsform, wenn das Frontend eine andere Antwort braucht, der Router, wenn
sich Pfad, Statuscodes oder Verdrahtung aendern. Die Modellnamen sind Teil des
veroeffentlichten OpenAPI-Schemas und bleiben deshalb, wie sie heissen.
"""

from collections.abc import Callable
from functools import partial
from typing import Annotated, Literal, Self, final

from fastapi import Depends, Request, Response
from pydantic import BaseModel, Field

from src.api.i18n import language_of
from src.contexts.identity.application.register_user import RegistrationAccepted

__all__ = [
    "CreatedHeaders",
    "GrantedSession",
    "RegisterUserResponse",
    "RegisteredUser",
    "TokenType",
    "apply_created_headers",
]

_SELF_URL = "/api/v1/identity/me"
"""Wohin die 201 zeigt: auf das angelegte Konto.

Der Endpunkt selbst entsteht mit #55; der Header zeigt schon dorthin, weil er
Teil des Vertrags dieser Antwort ist und nicht Teil jenes Endpunkts.
"""

type TokenType = Literal["Bearer"]
"""Das Schema, in dem der Access-Token vorzulegen ist (RFC 6750).

Steht ohne Matcher im Vertrag und ist damit bindend.

Das Feld traegt bewusst **keinen** Default: ein Default naehme es aus `required`
des Schemas. Der Wert wird an der Aufrufstelle gesetzt.
"""


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

    @classmethod
    def to_response(cls, accepted: RegistrationAccepted) -> Self:
        """Bilde den Ausgang des Use Case auf die Vertragsform ab.

        Der Use Case gibt die vier Sitzungsfelder flach heraus; ihre Gliederung
        unter `user` und `session` ist Sache dieser Grenze und steht deshalb
        hier.
        """
        return cls(
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


def _created_headers(response: Response, request: Request) -> Callable[[], None]:
    """Binde `apply_created_headers` an Anfrage und Antwort dieses Aufrufs.

    Zurueckgegeben wird ein Aufruf und nicht direkt gesetzt: eine Dependency
    laeuft **vor** dem Endpunkt und damit auch dann, wenn die Registrierung
    abgelehnt wird. So setzt der Endpunkt die Kopfzeilen selbst, im Zweig, der
    die 201 baut.
    """
    return partial(apply_created_headers, response, request)


type CreatedHeaders = Annotated[Callable[[], None], Depends(_created_headers)]
"""Die Kopfzeilen der 201, fertig gebunden - aufzurufen im 201-Zweig."""


def apply_created_headers(response: Response, request: Request) -> None:
    """Setze die Kopfzeilen, die zur 201 dieses Endpunkts gehoeren.

    `Cache-Control` und `X-Request-Id` stehen **nicht** hier: die setzt
    `ResponseEnvelopeMiddleware` fuer jede Antwort des Hosts.

    Nicht in eine Middleware zu verschieben: `IdempotencyKeyMiddleware` zeichnet
    `location` und `content-language` auf und spielt sie beim
    Wiederholungsaufruf zurueck (`REPLAYED_HEADERS`). Weiter aussen gesetzt,
    klebte ein frisch ausgehandelter Sprachkopf auf einem aufgezeichneten
    Koerper.
    """
    response.headers["Content-Language"] = language_of(request)
    response.headers["Location"] = _SELF_URL
