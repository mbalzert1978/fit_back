"""Domaene des Identity-Context - Aggregatwurzel, Value Objects, Ports, Operationen.

Physisch nach `entities/`, `value_objects/`, `ports/` gegliedert, im Namespace
aber bewusst flach: Value-Object-Ergebnisse, Entitaeten und Fehler referenzieren
einander, echte Unterpakete mit eigenen Re-Exports erzeugten dabei zirkulaere
Importe (.rules/python/python-feature-slices.md).

Diese Schicht haengt ausschliesslich an der stdlib und am `Result` des Shared
Kernel - maschinell abgesichert durch den `domain-purity`-Contract in setup.cfg.
"""

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
    EmailLocalPartHasInvalidCharacters,
    EmailLocalPartHasMisplacedDot,
    EmailLocalPartMissing,
    EmailLocalPartTooLong,
    EmailNeedsExactlyOneAtSign,
    UnencodableDomainLabel,
)
from src.contexts.identity.domain.entities.user import User, register
from src.contexts.identity.domain.errors import DomainError, EmailAlreadyRegistered
from src.contexts.identity.domain.events import UserRegistered
from src.contexts.identity.domain.ports.idn_encoder import IdnEncoder
from src.contexts.identity.domain.ports.password_hasher import PasswordHasher
from src.contexts.identity.domain.ports.user_registry import UserRegistry
from src.contexts.identity.domain.value_objects.account_status import (
    AccountStatus,
    Active,
    PendingDeletion,
    Suspended,
    account_status_tag,
)
from src.contexts.identity.domain.value_objects.display_name import DisplayName
from src.contexts.identity.domain.value_objects.email import Email
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
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.identity.domain.value_objects.user_time_zone import (
    DEFAULT_TIME_ZONE_ID,
    UserTimeZone,
)

__all__ = [
    "DEFAULT_LOCALE",
    "DEFAULT_TIME_ZONE_ID",
    "AccountStatus",
    "Active",
    "DisplayName",
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
    "EmailLocalPartHasInvalidCharacters",
    "EmailLocalPartHasMisplacedDot",
    "EmailLocalPartMissing",
    "EmailLocalPartTooLong",
    "EmailNeedsExactlyOneAtSign",
    "English",
    "German",
    "IdnEncoder",
    "Locale",
    "Password",
    "PasswordHash",
    "PasswordHasher",
    "PendingDeletion",
    "Suspended",
    "UnencodableDomainLabel",
    "User",
    "UserId",
    "UserRegistered",
    "UserRegistry",
    "UserTimeZone",
    "account_status_tag",
    "hydrate_locale",
    "locale_tag",
    "parse_locale",
    "register",
]
