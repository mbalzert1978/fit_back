"""Uebersetzt, was FastAPI selbst wirft, in das RFC-7807-Format.

Fachliche Fehlausgaenge laufen bewusst nicht hierueber - die tragen die Slices in ihrer
Response-Union.
"""

import logging
from dataclasses import asdict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ErrorDetails

from src.api.i18n import language_of, resources_of, translate
from src.api.problem_details import translated_problem
from src.api.request_validation_errors import (
    BodyNotAnObject,
    ExtraForbidden,
    FieldRequired,
    FieldTypeError,
    FieldValueRejected,
    JsonInvalid,
    RequestValidationFault,
)

logger = logging.getLogger(__name__)

_BODY_AS_A_WHOLE = "body"
"""Schluessel fuer Fehler, die kein einzelnes Feld betreffen, sondern den ganzen Body."""


def _field_of(error: ErrorDetails) -> str:
    """Lies den Feldnamen aus der Fehler-Position, ohne den `body`-Rahmen."""
    return ".".join(str(part) for part in error["loc"] if part != "body")


HANDLED_PYDANTIC_ERROR_TYPES = frozenset(
    {
        "missing",
        "extra_forbidden",
        "json_invalid",
        "string_type",
        "model_attributes_type",
        "value_error",
    }
)
"""Die Pydantic-Fehlertypen, die an diesem Handler ankommen koennen.

Gemessen statt geschaetzt: `tests/api/test_pydantic_error_contract.py` haelt die Menge in
beide Richtungen fest.
"""


def _fault_of(error: ErrorDetails) -> RequestValidationFault:
    """Uebersetze einen Pydantic-Fehler in unseren eigenen Fall.

    **Ausnahme, keine Vorlage.** `.rules/python/python-error-handling.md` schreibt
    `assert_never` als letzten Zweig vor, und die Regel gilt unveraendert; hier steht ein
    Wurf, weil `error["type"]` ein `str` ist und keine geschlossene Fallmenge hat.
    """
    field = _field_of(error)
    error_type = error["type"]
    match error_type:
        case "missing":
            return FieldRequired(field)
        case "extra_forbidden":
            return ExtraForbidden(field)
        case "json_invalid":
            return JsonInvalid()
        case "string_type":
            return FieldTypeError(field)
        case "model_attributes_type":
            return BodyNotAnObject()
        case "value_error":
            return FieldValueRejected(field)
        case _:
            msg = (
                f"Unbekannter Pydantic-Fehlertyp {error_type!r} am Exception-Handler. "
                "`_fault_of` in src/api/exception_handlers.py bildet ihn auf keinen Fall ab, "
                "und ein Auffangzweig wuerde dem Aufrufer eine falsche Begruendung nennen. "
                "Einen eigenen Fall in src/api/request_validation_errors.py anlegen, hier "
                "abbilden, den Text in beide Sprachdateien schreiben und den Typ in "
                "HANDLED_PYDANTIC_ERROR_TYPES aufnehmen."
            )
            raise ValueError(msg)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Beantworte einen strukturellen Request-Fehler als RFC-7807-ProblemDetails."""
    language = language_of(request)
    resources = resources_of(request)

    errors_dict: dict[str, list[str]] = {}
    for error in exc.errors():
        fault = _fault_of(error)
        field = getattr(fault, "field", "") or _BODY_AS_A_WHOLE
        errors_dict.setdefault(field, []).append(
            translate(resources, fault.code, asdict(fault), language)
        )

    logger.info(
        "Validation error at %s: %s fields",
        str(request.url.path),
        len(errors_dict),
    )
    return translated_problem(
        request,
        # 422 und nicht 400: lesbares JSON, nur der Inhalt hat die Regeln nicht
        # bestanden (RFC 9110 Abschnitt 15.5.21); der Pact nennt den Code ohne Matcher.
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation-failed",
        errors=errors_dict or None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registriere die Exception-Handler an der App.

    Ueber den Dekorator und nicht ueber `app.add_exception_handler(...)`: Starlette
    deklariert den Parameter dort als `Callable[[Request, Exception], ...]`, was unseren
    auf `RequestValidationError` verengten Handler kontravariant nicht annimmt.
    """
    app.exception_handler(RequestValidationError)(validation_exception_handler)
