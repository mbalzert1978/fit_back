"""Die Antwortform des Frontend-Vertrags von `POST /api/v1/identity/register`.

Hier steht **nur**, wie die 201 aussieht: die drei Modelle des `data`-Teils und
das Token-Schema, das eines ihrer Felder bindet. Kein Routing, keine
Dependencies, keine Fachentscheidung.

Getrennt vom Router, weil beide sich aus verschiedenen Gruenden aendern: die
Vertragsform, wenn das Frontend eine andere Antwort braucht, der Router, wenn
sich Pfad, Statuscodes oder Verdrahtung aendern. Die Modellnamen sind Teil des
veroeffentlichten OpenAPI-Schemas und bleiben deshalb, wie sie heissen.
"""

from typing import Literal, final

from pydantic import BaseModel, Field

__all__ = [
    "GrantedSession",
    "RegisterUserResponse",
    "RegisteredUser",
    "TokenType",
]

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
