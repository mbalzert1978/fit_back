"""Abbildung von Aggregaten auf die veroeffentlichten Ereignisse dieses Context.

Die Ereignisse selbst liegen in `contracts/` - sie gehoeren der Aussenseite.
Hier steht nur, *welcher Ausschnitt* eines Aggregats hinausgeht, und das ist eine
fachliche Entscheidung der Domaene, keine Verdrahtungsfrage.
"""

from src.contexts.identity.contracts import UserRegistered
from src.contexts.identity.domain.entities.user import User
from src.contexts.identity.domain.value_objects.locale import locale_tag

__all__ = ["user_registered"]


def user_registered(user: User) -> UserRegistered:
    """Melde die abgeschlossene Registrierung - genau der Ausschnitt aus dem Vertrag.

    Welche Felder das sind, entscheidet nicht diese Funktion, sondern die
    Beispiel-Dateien unter `contracts/events/user_registered/examples/`. Weicht
    der Aufbau hier davon ab, faellt der Contract-Spec um.
    """
    return UserRegistered(
        user_id=str(user.id),
        email=user.email.value,
        locale=locale_tag(user.locale),
        time_zone_id=user.time_zone.value,
        occurred_at=user.registered_at,
    )
