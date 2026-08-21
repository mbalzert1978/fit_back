"""Das OpenAPI-Schema der 201 von `POST /api/v1/identity/register`.

Die camelCase-Schluessel des 201-Koerpers stehen ohne Matcher im Pact und sind
damit bindend. Dokumentiert sind sie aber nur so lange, wie der Erfolgszweig ein
Response-Model zurueckgibt - faellt er auf eine `JSONResponse` zurueck, bleiben
die Vertragstests gruen und das Schema verschwindet still. Genau das faengt
dieser Test ab.

Die App wird um den Router allein gebaut: `app.openapi()` liest nur die
Routen-Deklaration, Umschlag und Datenbank spielen dafuer keine Rolle.
"""

from typing import Any

from fastapi import FastAPI
from src.api.identity import register_user_router

_SESSION_KEYS = {
    "accessToken",
    "expiresIn",
    "refreshToken",
    "refreshExpiresIn",
    "tokenType",
}


def test_die_201_ist_mit_konto_und_sitzung_dokumentiert() -> None:
    """Der 201-Koerper traegt `user` und `session`, und die Sitzung alle fuenf Schluessel."""
    app = FastAPI()
    app.include_router(register_user_router)
    schema = app.openapi()
    components: dict[str, dict[str, Any]] = schema["components"]["schemas"]

    def resolve(reference: dict[str, Any]) -> dict[str, Any]:
        assert "$ref" in reference, (
            f"Kein Model hinter dieser Stelle, nur {reference} - der Zweig gibt "
            "vermutlich wieder eine nackte `JSONResponse` zurueck."
        )
        return components[reference["$ref"].removeprefix("#/components/schemas/")]

    post = schema["paths"]["/api/v1/identity/register"]["post"]
    body = resolve(post["responses"]["201"]["content"]["application/json"]["schema"])

    assert set(body["properties"]) == {"user", "session"}
    assert set(resolve(body["properties"]["session"])["required"]) == _SESSION_KEYS
