"""Die konkreten Behaviors, die in eine Pipeline gehaengt werden koennen.

Je Aufgabe ein eigenes Modul, siehe
docs/decisions/2026-08-17-0937-pipeline-als-behavior-kette-im-shared-kernel.md.
Heute genau eines - die Eingabe-Validierung.
"""

from src.contexts.shared_kernel.behaviors.validating import validating

__all__ = ["validating"]
