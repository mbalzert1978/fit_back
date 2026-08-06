"""Aggregatwurzel User - identitaetsbasierte Gleichheit, ausschliesslich Value Objects."""

from datetime import datetime
from typing import final

from src.contexts.identity.domain.value_objects.account_status import AccountStatus, Active
from src.contexts.identity.domain.value_objects.display_name import DisplayName
from src.contexts.identity.domain.value_objects.email import Email
from src.contexts.identity.domain.value_objects.locale import Locale
from src.contexts.identity.domain.value_objects.password_hash import PasswordHash
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.identity.domain.value_objects.user_time_zone import UserTimeZone

__all__ = ["User", "register"]


@final
class User:
    """Der Kontoinhaber - Aggregatwurzel des Identity-Context.

    Zwei User sind genau dann gleich, wenn ihre Identitaet gleich ist; ein
    geaenderter Anzeigename macht sie nicht zu einem anderen User. Erzeugt wird
    die Wurzel ueber die Factory `register`, nie ueber diesen Konstruktor von
    ausserhalb des Moduls.
    """

    def __init__(
        self,
        user_id: UserId,
        email: Email,
        password_hash: PasswordHash,
        display_name: DisplayName,
        time_zone: UserTimeZone,
        locale: Locale,
        status: AccountStatus,
        registered_at: datetime,
    ) -> None:
        """Setze den vollstaendigen Zustand der Wurzel aus bereits gueltigen Value Objects."""
        self.id = user_id
        self.email = email
        self.password_hash = password_hash
        self.display_name = display_name
        self.time_zone = time_zone
        self.locale = locale
        self.status = status
        self.registered_at = registered_at

    def __eq__(self, other: object) -> bool:
        """Vergleiche ueber die Identitaet, nicht ueber die Attribute."""
        return isinstance(other, User) and self.id == other.id

    def __hash__(self) -> int:
        """Hashe ueber die Identitaet, passend zu `__eq__`."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Zeige Identitaet und E-Mail - nie den Passwort-Hash."""
        return f"User(id={self.id}, email={self.email.value!r})"


def register(
    user_id: UserId,
    email: Email,
    password_hash: PasswordHash,
    display_name: DisplayName,
    time_zone: UserTimeZone,
    locale: Locale,
    registered_at: datetime,
) -> User:
    """Lege einen neuen, aktiven User an.

    Infallibel: jedes Feld ist bereits ein gueltiges Value Object, und der
    Anfangsstatus eines frisch registrierten Kontos ist per Definition `Active`.
    Die einzige Invariante, die hier *nicht* entschieden werden kann - die
    Eindeutigkeit der E-Mail - gehoert dem `UserRegistry`-Port.
    """
    return User(
        user_id=user_id,
        email=email,
        password_hash=password_hash,
        display_name=display_name,
        time_zone=time_zone,
        locale=locale,
        status=Active(),
        registered_at=registered_at,
    )
