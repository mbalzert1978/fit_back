"""Erfuellt die public Naht `IdnLabels` ueber die `idna`-Bibliothek.

Implementiert **nicht** den Domain-Port `IdnEncoder` - das tut
`application/register_user/adapters/idn_encoder_adapter.py`. Dieses Modul kennt
die Domaene nicht: es spricht Primitive hinein und die Ergebnis-Union der Naht
heraus, sonst nichts.

Warum die Domaene das ueberhaupt fragen muss: ob `उदाहरण` ein gueltiges
IDN-Label ist und wie seine ASCII-Form lautet, entscheiden IDNA 2008 und UTS-46
anhand von Unicode-Tabellen (erlaubte Codepoints, Normalisierung, Bidi- und
Kontextregeln, Punycode). Das nachzubauen waere kein Fachwissen dieses Projekts,
sondern eine schlechtere Kopie einer Bibliothek.
"""

from typing import final

import idna

from src.contexts.identity.application.register_user.abstractions import (
    AsciiLabel,
    LabelEncoding,
    LabelRejected,
)

__all__ = ["IdnaLabels"]


@final
class IdnaLabels:
    """Erfuellt `IdnLabels` ueber IDNA 2008 mit UTS-46-Vorverarbeitung."""

    def to_ascii(self, label: str) -> LabelEncoding:
        """Wandle ein Label nach Punycode um.

        Das einzige `try`/`except` des Slice, und genau am richtigen Ort: hier
        liegt die Naht zur Bibliothek, und der Vertrag der Naht erklaert den
        Fehlschlag bereits ueber seine Ergebnis-Union
        (.rules/python/python-error-handling.md, "Nur an der IO-Naht fangen").
        """
        try:
            return AsciiLabel(idna.encode(label, uts46=True).decode("ascii"))
        except idna.IDNAError as error:
            return LabelRejected(str(error))
