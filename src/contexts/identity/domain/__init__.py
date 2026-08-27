"""Domaene des Identity-Context - Aggregatwurzel, Value Objects, Ports, Operationen.

Physisch nach `entities/`, `value_objects/`, `ports/` gegliedert, im Namespace
aber bewusst flach: Value-Object-Ergebnisse, Entitaeten und Fehler referenzieren
einander, echte Unterpakete mit eigenen Re-Exports erzeugten dabei zirkulaere
Importe (.rules/python/python-feature-slices.md).

Diese Schicht haengt ausschliesslich an der stdlib und am `Result` des Shared
Kernel - maschinell abgesichert durch den `domain-purity`-Contract in setup.cfg.
"""

from src.contexts.identity.domain.display_name_errors import (
    DisplayNameError,
    DisplayNameIsEmpty,
    DisplayNameTooLong,
    DisplayNameTooShort,
)
from src.contexts.identity.domain.email_errors import (
    EmailAddressLiteralInvalid,
    EmailDomainHasEmptyLabel,
    EmailDomainLabelHasEdgeHyphen,
    EmailDomainLabelHasInvalidCharacters,
    EmailDomainLabelTooLong,
    EmailDomainMissing,
    EmailDomainTooLong,
    EmailError,
    EmailHasWhitespace,
    EmailIsEmpty,
    EmailLocalPartHasInvalidCharacters,
    EmailLocalPartHasMisplacedDot,
    EmailLocalPartMissing,
    EmailLocalPartTooLong,
    EmailNeedsExactlyOneAtSign,
    UnencodableDomainLabel,
)
from src.contexts.identity.domain.entities.refresh_token import RefreshToken
from src.contexts.identity.domain.entities.user import User, UserFactory
from src.contexts.identity.domain.errors import DomainError, EmailAlreadyRegistered
from src.contexts.identity.domain.events import user_registered
from src.contexts.identity.domain.locale_errors import (
    LocaleError,
    LocaleIsEmpty,
    LocaleNotSupported,
)
from src.contexts.identity.domain.password_errors import (
    PasswordError,
    PasswordTooLong,
    PasswordTooShort,
)
from src.contexts.identity.domain.password_hash_errors import PasswordHashError, PasswordHashIsEmpty
from src.contexts.identity.domain.ports.idn_encoder import IdnEncoder, IdnEncoderError
from src.contexts.identity.domain.ports.password_hasher import PasswordHasher
from src.contexts.identity.domain.ports.session_issuer import SessionIssuer
from src.contexts.identity.domain.ports.user_registry import UserRegistry, UserRegistryError
from src.contexts.identity.domain.user_creation_errors import (
    DisplayNameRejected,
    EmailRejected,
    LocaleRejected,
    PasswordRejected,
    TimeZoneRejected,
    UserCreationError,
    UserRejected,
)
from src.contexts.identity.domain.user_id_errors import UserIdError, UserIdMalformed
from src.contexts.identity.domain.user_time_zone_errors import (
    UserTimeZoneError,
    UserTimeZoneIsEmpty,
    UserTimeZoneUnknown,
)
from src.contexts.identity.domain.value_objects.account_status import (
    AccountStatus,
    Active,
    PendingDeletion,
    Suspended,
    account_status_tag,
)
from src.contexts.identity.domain.value_objects.display_name import DisplayName
from src.contexts.identity.domain.value_objects.email import Email
from src.contexts.identity.domain.value_objects.issued_credentials import IssuedCredentials
from src.contexts.identity.domain.value_objects.locale import (
    DEFAULT_LOCALE,
    English,
    German,
    Locale,
    hydrate_locale,
    locale_tag,
    parse_locale,
)
from src.contexts.identity.domain.value_objects.password import Password
from src.contexts.identity.domain.value_objects.password_hash import PasswordHash
from src.contexts.identity.domain.value_objects.refresh_token_id import RefreshTokenId
from src.contexts.identity.domain.value_objects.token_hash import TokenHash
from src.contexts.identity.domain.value_objects.token_lifetime import (
    ACCESS_TOKEN_MAXIMUM_SECONDS,
    REFRESH_TOKEN_MAXIMUM_SECONDS,
    TokenLifetime,
)
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.identity.domain.value_objects.user_time_zone import (
    DEFAULT_TIME_ZONE_ID,
    UserTimeZone,
)

__all__ = [
    "ACCESS_TOKEN_MAXIMUM_SECONDS",
    "DEFAULT_LOCALE",
    "DEFAULT_TIME_ZONE_ID",
    "REFRESH_TOKEN_MAXIMUM_SECONDS",
    "AccountStatus",
    "Active",
    "DisplayName",
    "DisplayNameError",
    "DisplayNameIsEmpty",
    "DisplayNameRejected",
    "DisplayNameTooLong",
    "DisplayNameTooShort",
    "DomainError",
    "Email",
    "EmailAddressLiteralInvalid",
    "EmailAlreadyRegistered",
    "EmailDomainHasEmptyLabel",
    "EmailDomainLabelHasEdgeHyphen",
    "EmailDomainLabelHasInvalidCharacters",
    "EmailDomainLabelTooLong",
    "EmailDomainMissing",
    "EmailDomainTooLong",
    "EmailError",
    "EmailHasWhitespace",
    "EmailIsEmpty",
    "EmailLocalPartHasInvalidCharacters",
    "EmailLocalPartHasMisplacedDot",
    "EmailLocalPartMissing",
    "EmailLocalPartTooLong",
    "EmailNeedsExactlyOneAtSign",
    "EmailRejected",
    "English",
    "German",
    "IdnEncoder",
    "IdnEncoderError",
    "IssuedCredentials",
    "Locale",
    "LocaleError",
    "LocaleIsEmpty",
    "LocaleNotSupported",
    "LocaleRejected",
    "Password",
    "PasswordError",
    "PasswordHash",
    "PasswordHashError",
    "PasswordHashIsEmpty",
    "PasswordHasher",
    "PasswordRejected",
    "PasswordTooLong",
    "PasswordTooShort",
    "PendingDeletion",
    "RefreshToken",
    "RefreshTokenId",
    "SessionIssuer",
    "Suspended",
    "TimeZoneRejected",
    "TokenHash",
    "TokenLifetime",
    "UnencodableDomainLabel",
    "User",
    "UserCreationError",
    "UserFactory",
    "UserId",
    "UserIdError",
    "UserIdMalformed",
    "UserRegistry",
    "UserRegistryError",
    "UserRejected",
    "UserTimeZone",
    "UserTimeZoneError",
    "UserTimeZoneIsEmpty",
    "UserTimeZoneUnknown",
    "account_status_tag",
    "hydrate_locale",
    "locale_tag",
    "parse_locale",
    "user_registered",
]
