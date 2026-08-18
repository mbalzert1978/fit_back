"""Die konkreten Behaviors, die in eine Pipeline gehaengt werden koennen.

Je Aufgabe eine Einheit: was ein Behavior *tut*, aendert sich aus einem anderen
Grund als die Frage, *wie* eine Kette gefaltet und gerufen wird. Letztere steht
einmal in [`../pipeline.py`](../pipeline.py); jedes Behavior hier haengt an
dieser Naht und an dem, was es fuer seine eigene Aufgabe braucht.

Heute genau eines - die Eingabe-Validierung. Transaktionsklammer, Idempotenz,
Messung und Logging kaemen als je eigenes Modul daneben, nicht als weiterer
Absatz in einem bestehenden.
"""

from src.contexts.shared_kernel.behaviors.validating import validating

__all__ = ["validating"]
