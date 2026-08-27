"""Port-Adapter des Use Case RegisterUser - der Anti-Corruption-Layer nach unten.

Hier und nur hier treffen sich die beiden Welten: die Domaene spricht Value
Objects und `Result[T, E]` mit der **eigenen, schmalen Fehler-Union ihres Ports**
(`UserRegistryError`, `IdnEncoderError`), die public Naht spricht Primitive und
ihre eigenen Ergebnis-Unions. Die Adapter uebersetzen in beide Richtungen und
fangen dabei nichts ab - erwartete Fehlschlaege sind bereits Ergebnistypen der
Naht.
"""

from src.contexts.identity.application.register_user.adapters.event_publisher_adapter import (
    EventPublisherAdapter,
)
from src.contexts.identity.application.register_user.adapters.idn_encoder_adapter import (
    IdnEncoderAdapter,
)
from src.contexts.identity.application.register_user.adapters.password_hasher_adapter import (
    PasswordHasherAdapter,
)
from src.contexts.identity.application.register_user.adapters.session_issuer_adapter import (
    SessionIssuerAdapter,
)
from src.contexts.identity.application.register_user.adapters.user_registry_adapter import (
    UserRegistryAdapter,
)

__all__ = [
    "EventPublisherAdapter",
    "IdnEncoderAdapter",
    "PasswordHasherAdapter",
    "SessionIssuerAdapter",
    "UserRegistryAdapter",
]
