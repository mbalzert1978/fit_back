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
    """Melde die abgeschlossene Registrierung - Identitaet und Sprache, sonst nichts."""
    return UserRegistered(
        user_id=str(user.id),
        locale=locale_tag(user.locale),
        occurred_at=user.registered_at,
    )
