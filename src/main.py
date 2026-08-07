"""Der Einstiegspunkt: Zusammenbau der Anwendung, sonst nichts.

Diese Datei enthaelt bewusst weder Fachlichkeit noch Konfigurationslogik. Sie
beantwortet genau zwei Fragen:

- **Woraus besteht die Anwendung?** Middleware, Exception-Handler und Router -
  alles auf Modulebene. Nichts davon darf im Lifespan entstehen: Starlette baut
  die Middleware-Kette beim ersten ASGI-Aufruf zusammen, und der erste
  ASGI-Aufruf *ist* der Lifespan-Aufruf. Ein `add_middleware` im Startup kommt
  also immer zu spaet - siehe
  `docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`.
- **Was lebt so lange wie der Prozess?** Engine, Ereignis-Registrierung,
  Outbox-Worker - der Lifespan legt sie an und raeumt sie weg, mehr nicht.

Die Konfiguration steht in `src/settings.py`, der Health-Endpunkt in
`src/api/health_router.py`; beides braucht man auch ohne laufende App.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.composition import build_engine, build_event_registry, run_outbox_worker
from src.api.exception_handlers import register_exception_handlers
from src.api.health_router import health_router
from src.api.i18n import load_resources
from src.api.identity import register_user_router
from src.contexts.shared_kernel.time_provider import SystemTimeProvider
from src.middleware.idempotency import IdempotencyKeyMiddleware
from src.middleware.unhandled_exceptions import UnhandledExceptionMiddleware
from src.settings import validate_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lege die Ressourcen des Prozesses an und raeume sie wieder weg."""
    settings = validate_settings()
    app.state.settings = settings

    # Lade und validiere i18n Resource-Files beim Start
    load_resources()
    logger.info("i18n Resource-Dateien geladen")

    app.state.engine = build_engine(settings.database_url)
    app.state.event_registry = build_event_registry()
    logger.info("Datenbank-Engine erstellt")

    try:
        async with run_outbox_worker(app.state.engine, app.state.event_registry):
            yield
    finally:
        await app.state.engine.dispose()
        logger.info("Datenbank-Engine geschlossen")


app = FastAPI(title="Fit-back API", lifespan=lifespan)

# Reihenfolge: `add_middleware` schiebt jeweils nach vorn, die zuletzt
# hinzugefuegte laeuft also **aussen**. Der Auffangpunkt fuer unbehandelte
# Ausnahmen muss aussen liegen - sonst sieht er nicht, was weiter innen
# hochkommt, auch nicht aus der Idempotenz-Pruefung selbst.
app.add_middleware(IdempotencyKeyMiddleware, time_provider=SystemTimeProvider())
app.add_middleware(UnhandledExceptionMiddleware)

# Rate-Limit- und CSRF-Middleware sind hier bewusst nicht verdrahtet: beide kamen
# aus 96b8f2c, wurden mit 4165fed zurueckgenommen (siehe
# docs/decisions/2026-08-05-0936-security-gate-triage-ticket-0001.md) und sind
# ueber den PR-Merge c30054d unbemerkt zurueckgekehrt - inklusive zweier Importe,
# die es nicht gibt (`fastapi.middleware.base`, `starlette.middleware.csrf`).

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(register_user_router)


def main() -> None:
    """Starte die Anwendung."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
