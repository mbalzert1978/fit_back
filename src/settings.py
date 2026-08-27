"""Konfiguration des Prozesses - gelesen aus der Umgebung, geprueft beim Start."""

import os
from functools import lru_cache
from typing import final

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import URL

__all__ = [
    "DEFAULT_ACCESS_TOKEN_LIFETIME",
    "DEFAULT_API_VERSION",
    "DEFAULT_REFRESH_TOKEN_LIFETIME",
    "JWT_SECRET_MINIMUM_LENGTH",
    "Settings",
    "TokenSettings",
    "get_api_version",
    "get_settings",
]

JWT_SECRET_MINIMUM_LENGTH = 32
"""RFC 7518 Abschnitt 3.2: der HMAC-Schluessel ist mindestens so lang wie der Hash."""

DEFAULT_API_VERSION = "1"
"""Die Version dieser API, wenn die Umgebung keine nennt - dieselbe wie im Pfadpraefix `/api/v1`."""

DEFAULT_ACCESS_TOKEN_LIFETIME = 900
"""15 Minuten in Sekunden - die Zusage aus BACKEND.md Abschnitt 0, Punkt 8."""

DEFAULT_REFRESH_TOKEN_LIFETIME = 5_184_000
"""60 Tage in Sekunden - dieselbe Zusage."""


@final
class TokenSettings(BaseModel):
    """Die Geltungsdauern der beiden Token, in Sekunden.

    Erfuellt `RegisterUserTokenOptions` - die Feldnamen sind deshalb die des
    Vertrags und nicht die der Umgebungsvariablen.

    Ohne eigene Grenzen: welche Dauer zulaessig ist, entscheidet `TokenLifetime`
    in der Domaene und sonst niemand
    (docs/decisions/2026-08-27-2115-die-obergrenze-der-geltungsdauer-steht-in-der-domaene.md).
    """

    access_token_seconds: int = DEFAULT_ACCESS_TOKEN_LIFETIME
    refresh_token_seconds: int = DEFAULT_REFRESH_TOKEN_LIFETIME


@final
class Settings(BaseModel):
    """Die Einstellungen der Anwendung, samt Pruefung ihrer Werte."""

    api_version: str = Field(default=DEFAULT_API_VERSION, min_length=1)
    """Was `meta.apiVersion` und `info.version` nennen.

    Wer sie verstellt, verstellt das Pfadpraefix der Router mit - sonst nennt die
    Antwort eine andere Version als der Pfad, unter dem sie kam.
    """

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="fit_back")
    db_user: str = Field(default="fit_user")
    db_password: str = Field(...)
    jwt_secret: str = Field(..., min_length=JWT_SECRET_MINIMUM_LENGTH, repr=False)
    """Das Signaturgeheimnis der Access-Token - ohne Default, weil ein bekannter Default
    eine Hintertuer waere
    (`docs/decisions/2026-08-05-1130-security-gate-triage-ticket-0002-und-agent-integritaets-incident.md`).
    """

    tokens: TokenSettings = Field(default_factory=TokenSettings)
    """Eigene Sektion, weil die beiden Werte zusammen gehoert und zusammen gereicht werden."""

    @property
    def database_url(self) -> URL:
        """Die eine Datenbank-URL des Prozesses.

        Siehe `docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`.
        Ueber `URL.create` und nicht ueber einen f-String: ein Passwort darf `@`, `:`,
        `/`, `%` und `#` enthalten, und `URL.create` maskiert sie selbst.
        """
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


def _required_from_environment(name: str) -> str:
    """Liest eine Umgebungsvariable, die keinen Standardwert hat.

    Wirft `ValueError` und nicht `KeyError`, damit `get_settings` den Fall in seinem
    bestehenden `except` einfaengt. Genannt wird der Name der Variable, nie ihr Wert.
    """
    value = os.getenv(name)
    if value is None:
        msg = f"Missing required environment variable: {name}"
        raise ValueError(msg)
    return value


@lru_cache(maxsize=1)
def get_api_version() -> str:
    """Die Version dieser API - allein aus `API_VERSION`, ohne den Rest der Konfiguration.

    Eigener Weg herein und nicht ueber `get_settings`: der Einstiegspunkt
    verdrahtet Middleware und OpenAPI-Nachtrag beim **Import**, und dort darf
    noch keine vollstaendige Umgebung noetig sein
    (`tests/api/test_app_startup.py`). Diese eine Angabe hat als einzige einen
    Default und braucht deshalb keinen.
    """
    return os.getenv("API_VERSION", DEFAULT_API_VERSION)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Die eine Konfiguration des Prozesses - gelesen und geprueft beim ersten Aufruf.

    Wirft `RuntimeError`, wenn etwas fehlt oder unbrauchbar ist; die Meldung nennt keinen
    Wert, weil ein Passwort im Spiel ist und sie im Log landet.
    """
    try:
        return Settings(
            api_version=get_api_version(),
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "fit_back"),
            db_user=os.getenv("DB_USER", "fit_user"),
            db_password=_required_from_environment("DB_PASSWORD"),
            jwt_secret=_required_from_environment("JWT_SECRET"),
            tokens=TokenSettings(
                access_token_seconds=int(
                    os.getenv("ACCESS_TOKEN_LIFETIME", str(DEFAULT_ACCESS_TOKEN_LIFETIME))
                ),
                refresh_token_seconds=int(
                    os.getenv("REFRESH_TOKEN_LIFETIME", str(DEFAULT_REFRESH_TOKEN_LIFETIME))
                ),
            ),
        )
    except (ValidationError, ValueError) as e:
        msg = "Configuration validation failed: invalid environment variables"
        raise RuntimeError(msg) from e
