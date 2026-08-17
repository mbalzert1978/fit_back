"""Naht zur IDN-Umwandlung - von diesem Use Case formuliert, nicht von der Bibliothek.

Wie jede public Naht dieses Slice: nur Primitive, eine **eigene** Tagged Union
als Ergebnis, kein `Result[T, E]`. Der Fehlerkanal der Domaene bleibt
domaenenseitig; hierher uebersetzt der Port-Adapter.

Der Vertrag ist bewusst schmaler als das, was eine IDN-Bibliothek anbietet
(Dekodierung, ganze Domains, Optionsflaggen): gebraucht wird genau eine Richtung
fuer genau ein Label.
"""

from dataclasses import dataclass
from typing import Protocol, final

__all__ = ["AsciiLabel", "IdnLabels", "LabelEncoding", "LabelRejected"]


@final
@dataclass(frozen=True, slots=True)
class AsciiLabel:
    """Das Label in seiner ASCII-Form (Punycode)."""

    value: str


@final
@dataclass(frozen=True, slots=True)
class LabelRejected:
    """Das Label ist nach IDNA/UTS-46 kein gueltiger Domainname-Bestandteil."""

    reason: str


type LabelEncoding = AsciiLabel | LabelRejected


class IdnLabels(Protocol):
    """Wandelt ein einzelnes Domain-Label in seine ASCII-Form."""

    def to_ascii(self, label: str) -> LabelEncoding:
        """Liefere die Punycode-Form oder die Ablehnung samt Begruendung."""
        ...
