"""Konfiguration des Prozesses - gelesen aus der Umgebung, geprueft beim Start.

Bewusst ein eigenes Modul und nicht Teil des Einstiegspunkts: die Konfiguration
wird auch von Werkzeugen gebraucht, die die Anwendung gar nicht hochfahren
(Migrationsskripte, Diagnosebefehle), und `main.py` soll nichts enthalten, was
man ohne laufende App wissen muss.
"""

import os
from typing import final

from pydantic import BaseModel, Field, ValidationError

__all__ = ["Settings", "validate_settings"]


@final
class Settings(BaseModel):
    """Die Einstellungen der Anwendung, samt Pruefung ihrer Werte."""

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="fit_back")
    db_user: str = Field(default="fit_user")
    db_password: str = Field(...)  # Pflichtangabe, kein Standardwert

    @property
    def database_url(self) -> str:
        """Die eine Datenbank-URL des Prozesses.

        Der Treiber ist asyncpg, gefahren wird er ueber SQLAlchemy - ein Weg,
        den sich Health-Check, Idempotency-Middleware und die Slices teilen
        (`docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`).
        """
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


def validate_settings() -> Settings:
    """Lies die Einstellungen aus der Umgebung und pruefe sie.

    Wirft `RuntimeError`, wenn etwas fehlt oder unbrauchbar ist - der Prozess
    soll in dem Fall gar nicht erst starten, statt beim ersten Zugriff
    umzufallen. Die Meldung nennt bewusst keinen Wert: hier steht ein Passwort
    im Spiel, und eine Startfehlermeldung landet im Log.
    """
    try:
        return Settings(
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "fit_back"),
            db_user=os.getenv("DB_USER", "fit_user"),
            db_password=os.getenv("DB_PASSWORD"),
        )
    except (ValidationError, ValueError) as e:
        raise RuntimeError("Configuration validation failed: invalid environment variables") from e
