"""Fehlerfall-Codes für i18n-Rendering am HTTP-Rand.

Ein Fehlerfall ist ein Return-Typ in einer Response-Union. Jeder Case trägt seinen Code
explizit als Klassenvariable oder Instance-Attribute — nicht abgeleitet aus dem Klassennamen,
sondern ein verwalterter API-Vertrag. Der Code wird beim Startup gegen die Resource-Files geprüft.
"""

from typing import Any

__all__ = ["has_error_code"]


def has_error_code(error_case: type[Any]) -> bool:
    """Prüfe, ob eine Error-Klasse ein `code`-Attribute (ClassVar oder Instance) hat.

    Wird zur Startup-Zeit aufgerufen, um zu verifizieren, dass jeder Fehlerfall einen Code trägt.
    """
    return hasattr(error_case, "code")
