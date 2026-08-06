"""Implementiert den Domain-Port `IdnEncoder` ueber die public Naht `IdnLabels`.

Die Infrastruktur implementiert **nie** direkt einen Domain-Port. Sie erfuellt
die Naht - primitive Ein- und Ausgabe, eigene Ergebnis-Union - und dieser Adapter
uebersetzt sie in die Sprache der Domaene: `Result[T, DomainError]`. Nur so
bleibt die Domaene austauschbar gegenueber der Bibliothek und die Bibliothek
unwissend ueber die Domaene.
"""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    AsciiLabel,
    IdnLabels,
    LabelRejected,
)
from src.contexts.identity.domain import DomainError, UnencodableDomainLabel
from src.contexts.shared_kernel import Err, Ok, Result

__all__ = ["IdnEncoderAdapter"]


@final
class IdnEncoderAdapter:
    """Uebersetzt Naht-Union -> Domaenen-`Result`."""

    def __init__(self, labels: IdnLabels) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder `idna`)."""
        self._labels = labels

    def to_ascii(self, label: str) -> Result[str, DomainError]:
        """Wandle ein Label um und melde die Ablehnung als Domaenenfehler."""
        match self._labels.to_ascii(label):
            case AsciiLabel(value=ascii_label):
                return Ok(ascii_label)
            case LabelRejected(reason=reason):
                return Err(UnencodableDomainLabel(label, reason))
