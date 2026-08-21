"""Exception-Handler des HTTP-Randes.

Uebersetzt, was FastAPI selbst wirft, in das RFC-7807-Format. Fachliche
Fehlausgaenge laufen **nicht** hierueber: die tragen die Slices in ihrer
Response-Union, und der Router waehlt daraus Statuscode und Body. Ein
Exception-basierter zweiter Fehlerkanal daneben waere genau die Verzweigung,
die man beim Lesen nicht mehr sieht.
"""

import logging
from dataclasses import asdict
from typing import assert_never

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.i18n import ResourcesCache, get_language_from_header, translate
from src.api.problem_details import problem
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
"""Schluessel fuer Fehler, die kein einzelnes Feld betreffen, sondern den ganzen Body.

Pydantic verortet kaputtes JSON als `("body", <Zeichenposition>)`. Diese Position ist kein
Feldname und hat in `errors` nichts verloren - dort steht sonst der Name, unter dem der
Aufrufer sein Feld wiedererkennt.
"""


def _field_of(error: dict[str, object]) -> str:
    """Lies den Feldnamen aus der Fehler-Position, ohne den `body`-Rahmen."""
    location = error.get("loc") or ()
    return ".".join(str(part) for part in location if part != "body")


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

Der Handler haengt **app-weit**, nicht an einem Modell - die Menge ist also nicht die
von `RegisterUserBody` allein. Fuenf Typen stammen aus dessen Form (fuenf `str`-Felder,
`extra="forbid"`, kein eigener Constraint); `value_error` kommt aus jedem Modell mit
einem `field_validator`.

Nicht geschaetzt, sondern gemessen: `tests/api/test_pydantic_error_contract.py` faehrt
die Modelle gegen jede Form kaputter Eingabe und vergleicht das Ergebnis mit dieser
Menge - in beide Richtungen, damit weder ein unbehandelter Typ noch ein toter Zweig
stehen bleibt.
"""


def _fault_of(error: dict[str, object]) -> RequestValidationFault:
    """Uebersetze einen Pydantic-Fehler in unseren eigenen Fall.

    Vollstaendige Aufzaehlung, siehe `HANDLED_PYDANTIC_ERROR_TYPES`.

    Kein beantworteter Auffangzweig, sondern `assert_never`. Pydantics Fehlertypen sind
    zwar eine fremde Fallmenge, aber ein Update, das daran etwas aendert, ist eine
    Aenderung, die wir adressieren muessen - sie still auf `FieldTypeError` abzubilden
    hiesse, dem Aufrufer eine falsche Begruendung zu nennen. Genau das ist vorher
    passiert: `model_attributes_type` (Body ist ein Array statt eines Objekts) wurde als "das Feld
    '' hat den falschen Typ" ausgegeben, mit leerem Feldnamen.

    Damit der Bruch nicht erst hier bei einem Nutzer auftritt, wird er zweimal frueher
    abgefangen: `verify_pydantic_contract` prueft beim Start, ob die Typen im
    installierten Pydantic noch existieren, und der Vertragstest prueft in der CI, ob
    sich ihr Verhalten geaendert hat.
    """
    field = _field_of(error)
    error_type = error.get("type")
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
            assert_never(error_type)


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

    logger.info(
        "Validation error at %s: %s fields",
        str(request.url.path),
        len(errors_dict),
    )
    return problem(
        request,
        # 422 und nicht 400: der Koerper war lesbares JSON, nur sein Inhalt hat
        # die Regeln nicht bestanden (RFC 9110 Abschnitt 15.5.21). Der Vertrag
        # des Frontends nennt den Code ohne Matcher, er ist damit bindend.
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation-failed",
        title,
        detail,
        errors_dict or None,
        language_tag=language,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registriere die Exception-Handler an der App."""
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
