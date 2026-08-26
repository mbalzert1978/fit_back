"""Konfiguration des Prozesses - gelesen aus der Umgebung, geprueft beim Start."""

import os
from functools import lru_cache
from typing import final

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import URL

__all__ = ["JWT_SECRET_MINIMUM_LENGTH", "Settings", "get_settings"]

JWT_SECRET_MINIMUM_LENGTH = 32
"""RFC 7518 Abschnitt 3.2: der HMAC-Schluessel ist mindestens so lang wie der Hash."""


@final
class Settings(BaseModel):
    """Die Einstellungen der Anwendung, samt Pruefung ihrer Werte."""

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
def get_settings() -> Settings:
    """Die eine Konfiguration des Prozesses - gelesen und geprueft beim ersten Aufruf.

    Wirft `RuntimeError`, wenn etwas fehlt oder unbrauchbar ist; die Meldung nennt keinen
    Wert, weil ein Passwort im Spiel ist und sie im Log landet.
    """
    try:
        return Settings(
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "fit_back"),
            db_user=os.getenv("DB_USER", "fit_user"),
            db_password=_required_from_environment("DB_PASSWORD"),
            jwt_secret=_required_from_environment("JWT_SECRET"),
        )
    except (ValidationError, ValueError) as e:
        msg = "Configuration validation failed: invalid environment variables"
        raise RuntimeError(msg) from e
