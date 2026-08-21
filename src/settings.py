"""Konfiguration des Prozesses - gelesen aus der Umgebung, geprueft beim Start.

Bewusst ein eigenes Modul und nicht Teil des Einstiegspunkts: die Konfiguration
wird auch von Werkzeugen gebraucht, die die Anwendung gar nicht hochfahren
(Migrationsskripte, Diagnosebefehle), und `main.py` soll nichts enthalten, was
man ohne laufende App wissen muss.
"""

import os
from functools import lru_cache
from typing import final

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import URL

__all__ = ["JWT_SECRET_MINIMUM_LENGTH", "Settings", "get_settings", "validate_settings"]

JWT_SECRET_MINIMUM_LENGTH = 32
"""RFC 7518 Abschnitt 3.2: der HMAC-Schluessel ist mindestens so lang wie der Hash.

Kuerzer nimmt `pyjwt` zwar an, warnt aber - und eine Warnung im Log ist kein
Schutz. Der Prozess soll mit einem zu kurzen Geheimnis gar nicht erst starten.
"""


@final
class Settings(BaseModel):
    """Die Einstellungen der Anwendung, samt Pruefung ihrer Werte."""

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="fit_back")
    db_user: str = Field(default="fit_user")
    db_password: str = Field(...)  # Pflichtangabe, kein Standardwert
    jwt_secret: str = Field(..., min_length=JWT_SECRET_MINIMUM_LENGTH, repr=False)
    """Das Signaturgeheimnis der Access-Token - Pflichtangabe, kein Standardwert.

    Ein Default waere hier keine Bequemlichkeit, sondern eine Hintertuer: wer
    ihn kennt, kann sich als jeder Nutzer ausgeben. Genau dieser Fall steht
    schon einmal in
    `docs/decisions/2026-08-05-1130-security-gate-triage-ticket-0002-und-agent-integritaets-incident.md`.
    """

    @property
    def database_url(self) -> URL:
        """Die eine Datenbank-URL des Prozesses.

        Der Treiber ist asyncpg, gefahren wird er ueber SQLAlchemy - ein Weg,
        den sich Health-Check, Idempotency-Middleware und die Slices teilen
        (`docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`).

        Zusammengesetzt ueber `URL.create`, **nicht** ueber einen f-String. Eine
        URL hat Trennzeichen mit Bedeutung - `@`, `:`, `/`, `%`, `#` -, und ein
        Passwort darf sie alle enthalten. Interpoliert man es roh, verschiebt ein
        einziges `@` die Grenze zwischen Zugangsdaten und Host: der Prozess
        verbindet sich dann gegen einen anderen Server oder gar nicht.
        `URL.create` nimmt die Bestandteile einzeln entgegen und maskiert sie
        selbst - damit gibt es keine Stelle mehr, an der man das vergessen kann.

        Nebeneffekt, der hier zaehlt: `str(...)` einer `URL` zeigt das Passwort
        als `***`. Landet die URL versehentlich in einem Log, geht das Geheimnis
        nicht mit.
        """
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
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
            jwt_secret=os.getenv("JWT_SECRET"),
        )
    except (ValidationError, ValueError) as e:
        msg = "Configuration validation failed: invalid environment variables"
        raise RuntimeError(msg) from e


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Die eine Konfiguration des Prozesses - gelesen beim ersten Aufruf.

    Der Cache ist nicht bloss Ersparnis: er macht diese Funktion zu *der* Quelle
    der Konfiguration. Wer sie aufruft, bekommt dasselbe Objekt, das der
    Lifespan beim Start geprueft hat - er ruft sie als Erstes auf und faengt
    sich den `RuntimeError` einer unbrauchbaren Umgebung dort ein, wo er
    hingehoert: beim Start, nicht bei der ersten Anfrage.

    Als Dependency benutzt man sie ueber `SettingsDep` (`src/api/composition.py`).
    Im Test wird nicht die Umgebung gebogen, sondern die Dependency
    ueberschrieben - `app.dependency_overrides[get_settings]`.

    Wer die Umgebung tatsaechlich neu lesen will, ruft `cache_clear()`; das
    brauchen nur Tests, die den Start selbst nachstellen.
    """
    return validate_settings()
