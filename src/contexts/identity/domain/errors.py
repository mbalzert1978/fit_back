"""Der eine, flache Fehlertyp des Identity-Context.

Ein Fall je Fehlerursache, jeder mit **typisierter Nutzlast statt vorformatiertem
Text**. Alle Domain-Ports, Domaenen-Regeln und Aggregat-Operationen dieses
Contexts sprechen `Result[T, DomainError]` mit **diesem** `E` - dadurch braucht
es an den Port-Grenzen keine Fehleruebersetzung.

Die Faelle liegen teils hier, teils in [`email_errors.py`](./email_errors.py)
(Importzyklus, dort begruendet) - die Union unten ist die vollstaendige
Aufzaehlung dessen, was in diesem Context schiefgehen kann, und waechst mit
jedem weiteren Use Case.

Die Formulierung fuer Menschen gehoert **nicht** hierher, sondern in die
Application-Schicht: die Domaene sagt, *was* der Fall ist, nicht *wie* er heisst.
Der vollstaendige `match` in `application/shared/domain_error_message.py` meldet
sofort, wenn zu einem neuen Fall die Meldung fehlt.
"""

from dataclasses import dataclass
from typing import final

from src.contexts.identity.domain.display_name_errors import DisplayNameError
from src.contexts.identity.domain.email_errors import EmailError
from src.contexts.identity.domain.locale_errors import LocaleError
from src.contexts.identity.domain.password_errors import PasswordError
from src.contexts.identity.domain.password_hash_errors import PasswordHashError
from src.contexts.identity.domain.user_id_errors import UserIdError
from src.contexts.identity.domain.user_time_zone_errors import UserTimeZoneError
from src.contexts.identity.domain.value_objects.email import Email

__all__ = ["DomainError", "EmailAlreadyRegistered"]


@final
@dataclass(frozen=True, slots=True)
class EmailAlreadyRegistered:
    """Die (normalisierte) E-Mail gehoert bereits einem anderen Konto.

    Traegt bewusst **nicht**, wem: der Slice gibt es nach aussen nie preis - wer
    hinter einer fremden Adresse steckt, geht dem Anfragenden nichts an - und der
    Bestand muesste es nach einem Schreibkonflikt in einer zweiten Abfrage
    nachschlagen, die bei nebenlaeufigem, noch nicht committetem Insert nichts
    faende. Ein Feld, das niemand liest und das den Schreibpfad unkorrekt macht.
    """

    email: Email


type DomainError = (
    EmailAlreadyRegistered
    | EmailError
    | PasswordError
    | DisplayNameError
    | LocaleError
    | PasswordHashError
    | UserIdError
    | UserTimeZoneError
)
