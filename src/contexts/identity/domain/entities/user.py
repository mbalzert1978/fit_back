"""Aggregatwurzel User - identitaetsbasierte Gleichheit, ausschliesslich Value Objects."""

from typing import Final, final

from src.contexts.identity.domain.ports.idn_encoder import IdnEncoder
from src.contexts.identity.domain.ports.password_hasher import PasswordHasher
from src.contexts.identity.domain.user_creation_errors import (
    UserRejected,
    display_name_rejection,
    email_rejection,
    locale_rejection,
    password_rejection,
    time_zone_rejection,
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

__all__ = ["User"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `create` unten hat ihn."""


type _CheckedFields = tuple[tuple[tuple[tuple[Email, Password], DisplayName], Locale], UserTimeZone]
"""Was die `zip_all`-Kette unten aufgetuermt hat - je ein Paar je Schritt.

Ein Alias und keine Klasse: entpackt wird die Form genau einmal, in `_assembled`.
Ein Buendel-Typ mit fuenf benannten Feldern waere derselbe Inhalt ein zweites
Mal, nur mit Konstruktor.
"""


@final
class User:
    """Der Kontoinhaber - Aggregatwurzel des Identity-Context.

    Zwei User sind genau dann gleich, wenn ihre Identitaet gleich ist; ein
    geaenderter Anzeigename macht sie nicht zu einem anderen User.

    Gebaut wird ausschliesslich ueber `create`. Der Konstruktor nimmt fertige
    Value Objects und prueft nichts mehr - er ist der letzte Schritt von `create`
    und kein zweiter Weg herein.
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

    @classmethod
    def create(  # noqa: PLR0913 -- Aggregate factory: five fields and three ports
        cls,
        *,
        email: str,
        password: str,
        display_name: str,
        locale: str,
        time_zone: str,
        idn: IdnEncoder,
        hasher: PasswordHasher,
        clock: TimeProvider,
    ) -> AsyncResult[User, UserRejected]:
        """Lege einen neuen, aktiven User aus Rohwerten an.

        Rohwerte und keine fertigen Value Objects: sonst entstuenden die VOs eine
        Schicht weiter aussen, und der Aufrufer entschiede, welche Regeln sie
        gesehen haben.

        `zip_all` und nicht `zip`: die Wurzel **sammelt** ihre Ablehnungen. Damit
        ist sie die einzige Stelle, an der eine Registrierung geprueft wird -
        frueher lief dieselbe Pruefung ein zweites Mal als Behavior vor der
        Pipeline, nur damit alle Befunde auf einmal gemeldet werden konnten.

        Kein `async def`, sondern ein `AsyncResult`: damit ist die Wurzel selbst
        schon ein Kettenglied, an das der Aufrufer den Bestand haengt.

        Die einzige Invariante, die hier *nicht* entschieden werden kann - die
        Eindeutigkeit der E-Mail - gehoert dem `UserRegistry`-Port.
        """
        return (
            Email.parse(email, idn)
            .map_err(email_rejection)
            .zip_all(Password.parse(password).map_err(password_rejection))
            .zip_all(DisplayName.parse(display_name).map_err(display_name_rejection))
            .zip_all(parse_locale(locale).map_err(locale_rejection))
            .zip_all(UserTimeZone.parse(time_zone).map_err(time_zone_rejection))
            .map_err(user_rejected)
            .bind_async(lambda fields: cls._assembled(fields, hasher, clock))
        )

    @classmethod
    async def _assembled(
        cls, fields: _CheckedFields, hasher: PasswordHasher, clock: TimeProvider
    ) -> Result[User, UserRejected]:
        """Setze die Wurzel aus den gepruefen Feldern zusammen.

        Eigener Schritt, weil das Hashen wartet: eine `zip_all`-Kette ist
        synchron. Der Aufruf scheitert nicht mehr - `Ok` ist der einzige Ausgang
        -, traegt die Fehlerform aber weiter, damit die Kette einen Typ behaelt.

        Identitaet, Hash und Zeitpunkt entstehen **hier** und werden nicht
        hereingereicht: sie gehoeren zum Anlegen, nicht zur Eingabe.
        """
        ((((address, secret), name), language), zone) = fields
        return Ok(
            cls(
                user_id=UserId.generate(),
                email=address,
                password_hash=await hasher.hash(secret),
                display_name=name,
                time_zone=zone,
                locale=language,
                status=Active(),
                registered_at=clock.now(),
                key=_KEY,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Vergleiche ueber die Identitaet, nicht ueber die Attribute."""
        return isinstance(other, User) and self.id == other.id

    def __hash__(self) -> int:
        """Hashe ueber die Identitaet, passend zu `__eq__`."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Zeige Identitaet und E-Mail - nie den Passwort-Hash."""
        return f"User(id={self.id}, email={self.email.value!r})"
