"""Domain-Port IdnEncoder - die Punycode-Umwandlung internationalisierter Labels.

Die Domaene *kann* diese Frage nicht selbst beantworten: ob `उदाहरण` ein
gueltiges IDN-Label ist und wie seine ASCII-Form lautet, entscheiden IDNA 2008
und UTS-46 anhand von Unicode-Tabellen (erlaubte Codepoints, Normalisierung,
Bidi- und Kontextregeln, Punycode). Das nachzubauen waere kein Fachwissen dieses
Projekts, sondern eine schlechtere Kopie einer Bibliothek.

Also formuliert die Domaene, was sie braucht, und ueberlaesst das *Wie* dem
Adapter - genau wie bei Persistenz oder Passwort-Hashing. Damit bleibt `domain/`
an der stdlib haengen (maschinell erzwungen durch den `domain-purity`-Contract
in setup.cfg), und die Bibliothek ist austauschbar.

Alles, was **ASCII** ist, bleibt bewusst bei den Regeln in `email.py`: Label-
Laenge, Bindestrich-Position und Zeichenvorrat sind dort ausformuliert, tragen
je einen eigenen `DomainError`-Fall und sind Fall fuer Fall getestet. Der Port
wird nur gefragt, wo ohne ihn geraten werden muesste.
"""

from typing import TYPE_CHECKING, Protocol

from src.contexts.shared_kernel import Result

if TYPE_CHECKING:  # Importzyklus: errors.py haengt ueber email.py an diesem Modul.
    from src.contexts.identity.domain.errors import DomainError

__all__ = ["IdnEncoder"]


class IdnEncoder(Protocol):
    """Uebersetzt ein einzelnes Domain-Label in seine ASCII-Form.

    Wie jeder Domain-Port ehrlich fehlbar, und wie jeder Domain-Port mit
    **demselben** flachen Fehlertyp des Contexts - nicht mit einem `str`.
    """

    def to_ascii(self, label: str) -> Result[str, DomainError]:
        """Liefere die Punycode-Form; `Err`, wenn das Label kein gueltiges IDN-Label ist."""
        ...
