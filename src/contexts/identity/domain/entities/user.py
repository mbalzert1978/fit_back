"""Aggregatwurzel User - identitaetsbasierte Gleichheit, ausschliesslich Value Objects."""

from dataclasses import dataclass
from typing import Final, final

from src.contexts.identity.domain.ports.idn_encoder import IdnEncoder
from src.contexts.identity.domain.ports.password_hasher import PasswordHasher
from src.contexts.identity.domain.user_creation_errors import (
    DisplayNameRejected,
    EmailRejected,
    LocaleRejected,
    PasswordRejected,
    TimeZoneRejected,
    UserRejected,
    rejection,
    user_rejected,
)
from src.contexts.identity.domain.value_objects.account_status import AccountStatus, Active
from src.contexts.identity.domain.value_objects.display_name import DisplayName
from src.contexts.identity.domain.value_objects.email import Email
from src.contexts.identity.domain.value_objects.locale import Locale, parse_locale
from src.contexts.identity.domain.value_objects.password import Password
from src.contexts.identity.domain.value_objects.password_hash import PasswordHash
from src.contexts.identity.domain.value_objects.user_id import UserId
from src.contexts.identity.domain.value_objects.user_time_zone import UserTimeZone
from src.contexts.shared_kernel import (
    AsyncResult,
    ConstructionKey,
    Ok,
    Result,
    TimeProvider,
    Timestamp,
    deny_foreign_key,
)

__all__ = ["User", "UserFactory"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `UserFactory` unten hat ihn."""


type _ZippedFields = tuple[tuple[tuple[tuple[Email, Password], DisplayName], Locale], UserTimeZone]
"""Was die `zip_all`-Kette aufgetuermt hat - je ein Paar je Schritt.

Die Reihenfolge der Klammern ist die Reihenfolge der Kette in `UserFactory.create`.
Entpackt wird die Form genau einmal, in `_checked`.
"""


@final
@dataclass(frozen=True, slots=True)
class _CheckedFields:
    """Die fuenf gepruefen Felder, aus denen die Wurzel entsteht - benannt statt verschachtelt."""

    email: Email
    password: Password
    display_name: DisplayName
    locale: Locale
    time_zone: UserTimeZone


def _checked(zipped: _ZippedFields) -> _CheckedFields:
    """Loese die Paar-Verschachtelung der Kette in benannte Felder auf."""
    ((((email, password), display_name), locale), time_zone) = zipped
    return _CheckedFields(email, password, display_name, locale, time_zone)


@final
class User:
    """Der Kontoinhaber - Aggregatwurzel des Identity-Context.

    Gebaut wird ausschliesslich ueber `UserFactory`. Der Konstruktor prueft
    nichts mehr; er ist deren letzter Schritt und kein zweiter Weg herein.
    """

    def __init__(  # noqa: PLR0913, PLR0917 -- Aggregate root with 8 typed value objects
        self,
        user_id: UserId,
        email: Email,
        password_hash: PasswordHash,
        display_name: DisplayName,
        time_zone: UserTimeZone,
        locale: Locale,
        status: AccountStatus,
        registered_at: Timestamp,
        *,
        key: ConstructionKey,
    ) -> None:
        """Setze den vollstaendigen Zustand der Wurzel aus bereits gueltigen Value Objects."""
        deny_foreign_key(key, _KEY)
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


@final
@dataclass(frozen=True, slots=True)
class UserFactory:
    """Der eine Weg zu einem `User` - haelt die drei Ports, die das Anlegen braucht.

    Die Ports stehen hier und nicht in `create`: sie gehoeren zur Fabrik, nicht
    zur Eingabe eines einzelnen Aufrufs (.rules/python/python-factories.md).
    """

    idn: IdnEncoder
    hasher: PasswordHasher
    clock: TimeProvider

    def create(
        self, *, email: str, password: str, display_name: str, locale: str, time_zone: str
    ) -> AsyncResult[User, UserRejected]:
        """Lege einen neuen, aktiven User aus Rohwerten an.

        Die einzige Stelle, an der eine Registrierung geprueft wird
        (docs/decisions/2026-08-26-2330-die-wurzel-sammelt-ihre-befunde-selbst.md).

        Die Eindeutigkeit der E-Mail wird hier **nicht** entschieden - sie
        gehoert dem `UserRegistry`-Port.
        """
        return (
            Email.parse(email, self.idn)
            .map_err(rejection(EmailRejected))
            .zip_all(Password.parse(password).map_err(rejection(PasswordRejected)))
            .zip_all(DisplayName.parse(display_name).map_err(rejection(DisplayNameRejected)))
            .zip_all(parse_locale(locale).map_err(rejection(LocaleRejected)))
            .zip_all(UserTimeZone.parse(time_zone).map_err(rejection(TimeZoneRejected)))
            .map_err(user_rejected)
            .map(_checked)
            .bind_async(self._assembled)
        )

    async def _assembled(self, fields: _CheckedFields) -> Result[User, UserRejected]:
        """Setze die Wurzel aus den gepruefen Feldern zusammen.

        Eigener Schritt, weil das Hashen wartet: eine `zip_all`-Kette ist
        synchron. Scheitern kann er nicht mehr - `Ok` ist der einzige Ausgang -,
        er traegt die Fehlerform nur weiter, damit die Kette einen Typ behaelt.

        Identitaet, Hash und Zeitpunkt entstehen **hier** und werden nicht
        hereingereicht.
        """
        return Ok(
            User(
                user_id=UserId.generate(),
                email=fields.email,
                password_hash=await self.hasher.hash(fields.password),
                display_name=fields.display_name,
                time_zone=fields.time_zone,
                locale=fields.locale,
                status=Active(),
                registered_at=self.clock.now(),
                key=_KEY,
            )
        )
