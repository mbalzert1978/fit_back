"""Die public Naht des Use Case RegisterUser.

Drei Eigenschaften machen das zur Naht *dieses* Use Case und nicht zu einem
geteilten Identity-Gateway (.rules/python/python-feature-slices.md):

1. Nur die Operationen, die `register_user` wirklich braucht - kein `save`,
   kein `delete`, kein `find_by_id`, die andere Use Cases spaeter brauchen.
2. Ueber die Naht wandern ausschliesslich Primitive. Kein Value Object, keine
   Entitaet, kein Aggregat; die Uebersetzung ist Sache der Port-Adapter.
3. Jede fallible Operation liefert ihre **eigene**, einfache Tagged Union -
   nicht `Result[T, DomainError]`. Der Fehlerkanal der Domaene bleibt drinnen.

Je Mitspieler ein eigener Vertrag: Nutzerbestand, Hash-Verfahren und
IDN-Umwandlung haben nichts miteinander zu tun und werden von verschiedenen
Dingen erfuellt.
"""

from src.contexts.identity.application.register_user.abstractions.idn_labels import (
    AsciiLabel,
    IdnLabels,
    LabelEncoding,
    LabelRejected,
)
from src.contexts.identity.application.register_user.abstractions.password_hasher import (
    RegisterUserPasswordHasher,
)
from src.contexts.identity.application.register_user.abstractions.user_store import (
    EmailTaken,
    NewUserRecord,
    RegisterUserUserStore,
    UserInsertion,
    UserStored,
)

__all__ = [
    "AsciiLabel",
    "EmailTaken",
    "IdnLabels",
    "LabelEncoding",
    "LabelRejected",
    "NewUserRecord",
    "RegisterUserPasswordHasher",
    "RegisterUserUserStore",
    "UserInsertion",
    "UserStored",
]
