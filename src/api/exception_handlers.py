"""Exception-Handler des HTTP-Randes.

Uebersetzt, was FastAPI selbst wirft, in das RFC-7807-Format. Fachliche
Fehlausgaenge laufen **nicht** hierueber: die tragen die Slices in ihrer
Response-Union, und der Router waehlt daraus Statuscode und Body. Ein
Exception-basierter zweiter Fehlerkanal daneben waere genau die Verzweigung,
die man beim Lesen nicht mehr sieht.
"""

import logging
from dataclasses import asdict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.i18n import ResourcesCache, get_language_from_header, translate
from src.api.problem_details import ProblemDetails
from src.api.request_validation_errors import (
    ExtraForbidden,
    FieldRequired,
    FieldTypeError,
    JsonInvalid,
    RequestValidationFault,
)

logger = logging.getLogger(__name__)

_BODY_AS_A_WHOLE = "body"
"""Schluessel fuer Fehler, die kein einzelnes Feld betreffen, sondern den ganzen Body.

Pydantic verortet kaputtes JSON als `("body", <Zeichenposition>)`. Diese Position ist kein
Feldname und hat in `errors` nichts verloren - dort steht sonst der Name, unter dem der
Aufrufer sein Feld wiedererkennt.
"""


def _field_of(error: dict[str, object]) -> str:
    """Lies den Feldnamen aus der Fehler-Position, ohne den `body`-Rahmen."""
    location = error.get("loc") or ()
    return ".".join(str(part) for part in location if part != "body")


def _fault_of(error: dict[str, object]) -> RequestValidationFault:
    """Uebersetze einen Pydantic-Fehler in unseren eigenen Fall.

    Vollstaendige Aufzaehlung dessen, was `RegisterUserBody` ueberhaupt ausloesen kann
    (fuenf `str`-Pflichtfelder, `extra="forbid"`, keine eigenen Constraints). Der
    Auffangzweig ist bewusst `FieldTypeError`: taucht ein bislang unbekannter
    Pydantic-Fehlertyp auf, bekommt der Aufrufer weiterhin eine uebersetzte,
    maschinenlesbare Antwort statt einer englischen Rohmeldung. Der Fall gehoert dann
    hier ergaenzt.
    """
    field = _field_of(error)
    match error.get("type"):
        case "missing":
            return FieldRequired(field)
        case "extra_forbidden":
            return ExtraForbidden(field)
        case "json_invalid":
            return JsonInvalid()
        case _:
            return FieldTypeError(field)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Beantworte einen strukturellen Request-Fehler als RFC-7807-ProblemDetails.

    Die Rohmeldung von Pydantic wird **nicht** durchgereicht: sie waere englisch,
    unabhaengig vom `Accept-Language`-Header, und damit haette `errors.*` je nach
    Fehlerursache mal einen eigenen Code und mal den Text einer fremden Bibliothek.
    Stattdessen wird jeder Fehler auf einen eigenen Fall abgebildet, der seinen Code
    traegt - genau wie die fachlichen Feldfehler aus dem Slice.
    """
    language = get_language_from_header(request.headers.get("accept-language"))
    resources: ResourcesCache = request.app.state.resources

    errors_dict: dict[str, list[str]] = {}
    for error in exc.errors():
        fault = _fault_of(error)
        # Der Schluessel kommt aus dem Fall, nicht ein zweites Mal aus den Rohdaten:
        # ein Fall ohne `field` betrifft den Body als Ganzes.
        field = getattr(fault, "field", "") or _BODY_AS_A_WHOLE
        errors_dict.setdefault(field, []).append(
            translate(resources, fault.code, asdict(fault), language)
        )

    title = translate(resources, "validation-failed", language=language)
    detail = translate(resources, "validation-failed-detail", language=language)

    problem = ProblemDetails(
        type="https://api.example/errors/validation-failed",
        title=title,
        status=status.HTTP_400_BAD_REQUEST,
        detail=detail,
        instance=str(request.url.path),
        errors=errors_dict or None,
    )
    logger.info(
        "Validation error at %s: %s fields",
        str(request.url.path),
        len(errors_dict),
    )
    response = JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
    response.headers["Content-Language"] = language
    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Registriere die Exception-Handler an der App."""
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
