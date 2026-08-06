"""Der letzte Auffangpunkt: was niemand behandelt hat, wird hier protokolliert.

Diese Middleware ist **kein** Fehlerkanal. Fachliche Fehlausgaenge tragen die
Slices in ihrer Response-Union, und der Router waehlt daraus Statuscode und Body
(siehe `docs/decisions/2026-08-06-1330-shared-kernel-neuschnitt.md`). Was hier
ankommt, ist per Definition **kein** Fachfall, sondern ein Programmierfehler
oder eine ausgefallene Ressource - etwas, das niemand vorhergesehen hat.

Genau deshalb steht sie hier und nicht als Exception-Handler an der App:
Starlettes eingebauter `ServerErrorMiddleware` gibt in Produktion eine nackte
`Internal Server Error`-Textantwort zurueck, ohne Format und ohne dass der
Stacktrace irgendwo mit Kontext festgehalten waere. Ein Aufrufer, der ueberall
sonst `application/problem+json` bekommt, bekaeme ausgerechnet im schlimmsten
Fall etwas anderes.

Zwei Zusagen macht sie, und nur diese zwei:

1. **Der Fehler wird vollstaendig protokolliert** - mit Stacktrace, Methode und
   Pfad, damit der Eintrag allein zur Diagnose reicht.
2. **Nach aussen geht nichts davon.** Der Aufrufer bekommt 500 als
   RFC-7807-Dokument ohne Details. Ein Stacktrace in der Antwort ist ein
   Informationsleck: er verraet Dateipfade, Bibliotheksversionen und oft genug
   Teile der Nutzdaten.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import final

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from src.api.problem_details import ProblemDetails

logger = logging.getLogger(__name__)

UNHANDLED_ERROR_TYPE = "https://api.example/errors/internal-server-error"

__all__ = ["UNHANDLED_ERROR_TYPE", "UnhandledExceptionMiddleware"]


@final
class UnhandledExceptionMiddleware(BaseHTTPMiddleware):
    """Faengt jede Exception, die keiner behandelt hat, protokolliert sie und antwortet mit 500."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Lass die Anfrage laufen und fange, was niemand sonst gefangen hat."""
        try:
            return await call_next(request)
        except Exception:
            # `exception` statt `error`: nur so landet der Stacktrace im Log -
            # und ohne ihn ist der Eintrag zur Diagnose wertlos.
            logger.exception(
                "Unbehandelte Ausnahme bei %s %s",
                request.method,
                request.url.path,
            )
            problem = ProblemDetails(
                type=UNHANDLED_ERROR_TYPE,
                title="Interner Serverfehler",
                status=HTTP_500_INTERNAL_SERVER_ERROR,
                # Bewusst nichtssagend: was schiefging, steht im Log, nicht in
                # der Antwort.
                detail="Die Anfrage konnte nicht verarbeitet werden.",
                instance=request.url.path,
            )
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content=problem.model_dump(exclude_none=True),
                media_type="application/problem+json",
            )
