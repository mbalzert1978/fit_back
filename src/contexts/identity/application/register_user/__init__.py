"""Use Case RegisterUser - die public Oberflaeche des Slice.

Was hier exportiert wird, ist alles, was der Slice nach aussen zusagt: das
Request-DTO, die Response-Union, die public Naht samt ihren Ergebnis-Unions, die
Verdrahtungs-Fabrik und die Test-API. Handler, Command, Mapper, Adapter und
Domaene sind bewusst **nicht** dabei - wer sie importiert, greift an der Naht
vorbei.
"""

from src.contexts.identity.application.register_user.abstractions import (
    AsciiLabel,
    EmailTaken,
    IdnLabels,
    IssuedSession,
    LabelEncoding,
    LabelRejected,
    NewUserRecord,
    RegisterUserEventLog,
    RegisterUserPasswordHasher,
    RegisterUserSessionTokens,
    RegisterUserUserStore,
    UserInsertion,
    UserStored,
)
from src.contexts.identity.application.register_user.pipeline import (
    RegisterUserPipeline,
    build_register_user_pipeline,
)
from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.application.register_user.response import (
    EmailAlreadyTaken,
    RegisterUserFailure,
    RegisterUserResponse,
    RegistrationAccepted,
    RegistrationInvalid,
)
from src.contexts.identity.application.register_user.test_api import RegisterUserTestApi

__all__ = [
    "AsciiLabel",
    "EmailAlreadyTaken",
    "EmailTaken",
    "IdnLabels",
    "IssuedSession",
    "LabelEncoding",
    "LabelRejected",
    "NewUserRecord",
    "RegisterUserEventLog",
    "RegisterUserFailure",
    "RegisterUserPasswordHasher",
    "RegisterUserPipeline",
    "RegisterUserRequest",
    "RegisterUserResponse",
    "RegisterUserSessionTokens",
    "RegisterUserTestApi",
    "RegisterUserUserStore",
    "RegistrationAccepted",
    "RegistrationInvalid",
    "UserInsertion",
    "UserStored",
    "build_register_user_pipeline",
]
