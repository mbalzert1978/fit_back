"""Der eine, flache Fehlertyp des Identity-Context.

Ein Fall je Fehlerursache, jeder mit typisierter Nutzlast statt vorformatiertem
Text. Alle Domain-Ports, Domaenen-Regeln und Aggregat-Operationen dieses
Contexts sprechen `Result[T, DomainError]` mit **diesem** `E` - dadurch braucht
es an den Port-Grenzen keine Fehleruebersetzung.

Die Union waechst mit jedem weiteren Use Case des Contexts (Login, ChangePassword,
RequestAccountDeletion). Heute traegt sie genau den einen Fehlschlag, den
`register_user` kennt; weitere Faelle kommen hinzu, sie werden nicht vorgezogen.

Formatfehler roher Eingaben gehoeren *nicht* hierher: ein Value Object meldet sie
als `Result[T, str]` aus seiner `parse`-Factory, bevor ueberhaupt eine Domaenen-
Operation laeuft (siehe .rules/python/python-error-handling.md).
"""

from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain.value_objects.email import Email
from src.contexts.identity.domain.value_objects.user_id import UserId

__all__ = ["DomainError", "EmailAlreadyRegistered"]


@final
@dataclass(frozen=True, slots=True)
class EmailAlreadyRegistered:
    """Die (normalisierte) E-Mail gehoert bereits einem anderen Konto."""

    email: Email
    registered_to: UserId


type DomainError = EmailAlreadyRegistered
