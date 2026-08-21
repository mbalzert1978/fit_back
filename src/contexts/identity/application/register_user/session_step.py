"""Der Schritt, der die Sitzung ausstellt: aufgenommener User -> `Registration`.

Eine eigene, benannte Stelle und keine Closure in der Fabrik: hier steht
Fachablauf - **wann** ein Token entsteht und woran sein Zeitpunkt haengt -, und
der gehoert nicht in das Modul, das nur verdrahtet.

Kein Behavior der Kette (`shared_kernel/pipeline.py`), obwohl es eines sein
koennte: ein Behavior traegt dieselbe Ein- und Ausgabe wie der Schritt, den es
umschliesst, und dieser Schritt **aendert** den Ausgabetyp - aus dem Aggregat
wird das Paar aus Aggregat und Sitzung. Als Behavior getarnt muesste der ganze
Kette der weitere Typ aufgezwungen werden, samt eines `Registration`, das schon
vor der Ausstellung existiert und keine Sitzung haette.
"""

from src.contexts.identity.application.register_user.abstractions import (
    RegisterUserSessionTokens,
)
from src.contexts.identity.application.register_user.errors import RegisterUserError
from src.contexts.identity.application.register_user.registration import Registration
from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.domain import User
from src.contexts.shared_kernel import Ok, Result
from src.contexts.shared_kernel.pipeline import Handler

__all__ = ["issuing_session"]


def issuing_session(
    step: Handler[RegisterUserRequest, User, RegisterUserError],
    sessions: RegisterUserSessionTokens,
) -> Handler[RegisterUserRequest, Registration, RegisterUserError]:
    """Lege die Ausstellung um den Schritt, der den User aufnimmt.

    Die Sitzung entsteht **nur** im Erfolgsfall - `bind_async` laesst den
    Fehlerkanal unberuehrt. Eine abgelehnte Registrierung bekommt keinen Token.

    Als Zeitpunkt der Ausstellung dient `registered_at` des Aggregats. Das ist
    dieselbe Uhrablesung, aus der auch die Nutzer-Zeile entsteht; eine zweite
    liesse Konto und Token um Millisekunden auseinanderliegen, ohne dass jemand
    davon etwas haette.
    """

    async def issue(user: User) -> Result[Registration, RegisterUserError]:
        session = await sessions.issue(str(user.id), user.registered_at.unix_seconds)
        return Ok(Registration(user, session))

    async def run(request: RegisterUserRequest) -> Result[Registration, RegisterUserError]:
        return await (await step(request)).bind_async(issue)

    return run
