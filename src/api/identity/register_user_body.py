"""Die Anfrageform des Frontend-Vertrags von `POST /api/v1/identity/register`.

Hier steht **nur**, wie der Rumpf hereinkommt: die fuenf Felder in der
camelCase-Schreibweise der Schnittstelle und ihre Uebersetzung in das public
Request-DTO des Slice.

Getrennt vom Router aus demselben Grund wie die beiden Antwortformen nebenan:
die Anfrageform aendert sich, wenn das Frontend einen anderen Rumpf schickt, der
Router, wenn sich Pfad, Statuscodes oder Verdrahtung aendern. Der Modellname ist
Teil des veroeffentlichten OpenAPI-Schemas und bleibt deshalb, wie er heisst.
"""

from typing import final

from pydantic import BaseModel, ConfigDict, Field

from src.contexts.identity.application.register_user import RegisterUserRequest

__all__ = ["RegisterUserBody"]


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
