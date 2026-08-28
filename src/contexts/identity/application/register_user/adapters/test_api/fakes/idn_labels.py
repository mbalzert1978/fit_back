"""In-Memory-Naht fuer IDN-Labels: reicht ASCII durch, lehnt alles andere ab.

Bewusst **kein** nachgebautes Punycode. Die Verhaltens-Specs des Slice arbeiten
ausschliesslich mit ASCII-Domains; was IDNA/UTS-46 mit einem Unicode-Label
machen, ist keine Frage dieses Use Case, sondern eine des `Email`-Value-Object -
und dort gegen die **echte** Bibliothek spezifiziert, in
`contexts/identity/specs/domain/test_email.py`.

Ein Fake, der Punycode nachbaut, wuerde die Spezifikation gegen sich selbst
pruefen. Deshalb sagt dieser hier ehrlich, dass er es nicht kann.
"""

from typing import final

from src.contexts.identity.application.register_user.abstractions import (
    AsciiLabel,
    LabelEncoding,
    LabelRejected,
)

__all__ = ["PassthroughIdnLabels"]


@final
class PassthroughIdnLabels:
    """Erfuellt `IdnLabels` fuer Specs mit ASCII-Domains."""

    def to_ascii(self, label: str) -> LabelEncoding:
        """Reiche ASCII-Labels durch; lehne internationalisierte ab."""
        if not label.isascii():
            return LabelRejected("Fake unterstuetzt keine internationalisierten Labels")
        return AsciiLabel(label)
