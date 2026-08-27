"""Die vollstaendige Aufzaehlung dessen, was im Identity-Context schiefgehen kann.

Ein Fall je Fehlerursache, jeder mit **typisierter Nutzlast statt vorformatiertem
Text**.

`DomainError` ist die **Summe** aller Faelle, nicht der eine `E`, den ein Port
spricht - jeder Port traegt seine eigene, schmale Fehler-Union
(`UserRegistryError` in [`ports/user_registry.py`](./ports/user_registry.py),
`IdnEncoderError` in [`ports/idn_encoder.py`](./ports/idn_encoder.py),
`EmailError` fuer `Email.parse` und so fort). Warum:
docs/decisions/2026-08-17-0933-fehler-union-je-port-statt-domainerror-als-sammeltyp.md.

Wozu die Summe trotzdem gebraucht wird: sie ist die Liste, gegen die die
Fehlercode- und i18n-Drift-Pruefungen zaehlen (`shared_kernel/coded_error.py`,
`tests/test_i18n_drift.py`) - "gibt es zu jedem Fall einen Code und eine
Textvorlage?" ist eine Frage an *alle* Faelle, nicht an die eines Ports.

Die Faelle liegen teils hier, teils in [`email_errors.py`](./email_errors.py)
(Importzyklus, dort begruendet); die Union unten waechst mit jedem weiteren
Use Case.

Die Formulierung fuer Menschen gehoert **nicht** hierher, sondern an den Rand:
die Domaene sagt, *was* der Fall ist, nicht *wie* er heisst. Dass zu jedem neuen
Fall auch eine Textvorlage existiert, melden die oben genannten Waechter.
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
