"""Duenne Erfuellungen der Slice-Nahten ueber die Outbox.

Eine Klasse je Use Case, ohne eigene Logik. Architektur-Begruendung (Richtung,
warum hier statt im Slice) siehe
`docs/decisions/2026-08-06-1120-outbox-mechanismus-statt-naht.md`.
"""

from src.infrastructure.outbox.publishers.identity_register_user import (
    RegisterUserOutbox,
)

__all__ = ["RegisterUserOutbox"]
