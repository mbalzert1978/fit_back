"""Allgemeine Textregeln - fail-fast, wiederverwendbar, ohne fachlichen Bezug.

Hierher gehoert nur, was in jedem Context dieselbe Frage ist **und** deren
Fehlerfall selbst allgemein ist. Eine Laengenregel erfuellt das zweite nicht -
ihr Fall traegt einen fachlichen Code - und steht deshalb bei ihrem Value Object.
"""

from dataclasses import dataclass
from typing import final

from src.contexts.shared_kernel.result import Err, Ok, Result

__all__ = ["NotBlankError", "TextIsEmpty", "not_blank"]


@final
@dataclass(frozen=True, slots=True)
class TextIsEmpty:
    """Der Text besteht nur aus Leerraum.

    Ohne Fehlercode: technisch und ohne Feldbezug. Wer ihn meldet, uebersetzt
    ihn vorher in seinen fachlichen Fall.
    """


type NotBlankError = TextIsEmpty


def not_blank(raw: str) -> Result[str, NotBlankError]:
    """Der Text besteht nicht nur aus Leerraum - und kommt getrimmt zurueck.

    Getrimmt, weil die Regel ohnehin trimmen muss, um zu urteilen: gaebe sie den
    Rohwert weiter, muesste jede folgende Regel es erneut tun.
    """
    trimmed = raw.strip()
    return Ok(trimmed) if trimmed else Err(TextIsEmpty())
