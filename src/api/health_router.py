"""Der Health-Endpunkt - beantwortet genau eine Frage: kommt die App an ihre Datenbank?

Bewusst ueber dieselbe Engine wie die Slices. Ein Health-Check, der sich eine
eigene Verbindung baut, prueft eine Verbindung, die mit der Verbindung der
Anfragen nichts zu tun hat - er meldet "gesund", waehrend jeder Aufruf an einer
erschoepften Engine haengt.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

__all__ = ["health_router"]

health_router = APIRouter(prefix="/api/v1", tags=["health"])


def _engine(request: Request) -> AsyncEngine | None:
    """Hole die Engine des Prozesses, solange es sie schon gibt."""
    return getattr(request.app.state, "engine", None)


@health_router.get("/health")
async def health_check(
    response: Response, engine: Annotated[AsyncEngine | None, Depends(_engine)]
) -> dict[str, str]:
    """Liefere 200, sobald die Datenbank erreichbar ist, sonst 503."""
    if engine is None:
        logger.warning("Health check: Datenbank nicht verfuegbar")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy"}

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Health check: Verbindung zur Datenbank fehlgeschlagen")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy"}

    return {"status": "healthy"}
