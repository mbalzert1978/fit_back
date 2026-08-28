"""Die public Naht des Use Case RegisterUser.

Eigene, schmale Vertraege statt eines geteilten Identity-Gateways
(.rules/python/python-feature-slices.md): nur die Operationen, die
`register_user` wirklich braucht, ausschliesslich Primitive ueber der Naht, und
je fallibler Operation ihre eigene, einfache Tagged Union statt `Result[T, E]`.

Je Mitspieler ein eigener Vertrag: Nutzerbestand, Hash-Verfahren und
IDN-Umwandlung haben nichts miteinander zu tun und werden von verschiedenen
Dingen erfuellt.
"""

from src.contexts.identity.application.register_user.abstractions.access_tokens import (
    RegisterUserAccessTokens,
)
from src.contexts.identity.application.register_user.abstractions.event_log import (
    RegisterUserEventLog,
)
from src.contexts.identity.application.register_user.abstractions.idn_labels import (
    AsciiLabel,
    IdnLabels,
    LabelEncoding,
    LabelRejected,
)
from src.contexts.identity.application.register_user.abstractions.password_hasher import (
    RegisterUserPasswordHasher,
)
from src.contexts.identity.application.register_user.abstractions.session_tokens import (
    MintedSecret,
    RefreshTokenRecord,
    RegisterUserSessionTokens,
)
from src.contexts.identity.application.register_user.abstractions.token_options import (
    RegisterUserTokenOptions,
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
    "MintedSecret",
    "NewUserRecord",
    "RefreshTokenRecord",
    "RegisterUserAccessTokens",
    "RegisterUserEventLog",
    "RegisterUserPasswordHasher",
    "RegisterUserSessionTokens",
    "RegisterUserTokenOptions",
    "RegisterUserUserStore",
    "UserInsertion",
    "UserStored",
]
