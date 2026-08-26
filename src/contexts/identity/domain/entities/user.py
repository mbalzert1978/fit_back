"""Aggregatwurzel User - identitaetsbasierte Gleichheit, ausschliesslich Value Objects."""

from typing import Final, final

from src.contexts.identity.domain.ports.idn_encoder import IdnEncoder
from src.contexts.identity.domain.ports.password_hasher import PasswordHasher
from src.contexts.identity.domain.user_creation_errors import (
    DisplayNameRejected,
    EmailRejected,
    LocaleRejected,
    PasswordRejected,
    TimeZoneRejected,
    UserCreationError,
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
    ConstructionKey,
    Err,
    Ok,
    Result,
    TimeProvider,
    Timestamp,
    deny_foreign_key,
)

__all__ = ["User"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `create` unten hat ihn."""


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
    async def create(  # noqa: PLR0913 -- Aggregate factory: five fields and three ports
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
    ) -> Result[User, UserCreationError]:
        """Lege einen neuen, aktiven User aus Rohwerten an.

        Rohwerte und keine fertigen Value Objects: sonst entstuenden die VOs eine
        Schicht weiter aussen, und der Aufrufer entschiede, welche Regeln sie
        gesehen haben. So kommt niemand an einen `User`, ohne dass jede Invariante
        dieser Wurzel gelaufen ist - und die VOs verlassen die Domaene nie.

        Identitaet, Hash und Zeitpunkt entstehen **hier** und werden nicht
        hereingereicht: sie gehoeren zum Anlegen, nicht zur Eingabe. Die drei
        Ports dafuer kommen per Dependency Injection, damit die Wurzel weder eine
        Uhr noch ein Hash-Verfahren kennt.

        Fehlbar, seit die Wurzel selbst parst: `Active` als Anfangsstatus steht
        weiterhin fest, aber ein Feld kann seine Regel verfehlen. Die einzige
        Invariante, die hier *nicht* entschieden werden kann - die Eindeutigkeit
        der E-Mail - gehoert nach wie vor dem `UserRegistry`-Port.
        """
        # Alle fuenf laufen, dann gewinnt der erste Fehler. Ein `bind` je Feld
        # waere fail-fast, verschraenkte die fuenf aber ineinander; die Parser
        # sind rein und billig, und ein flacher `match` bleibt lesbar
        # (.rules/python/python-error-handling.md).
        match (
            Email.parse(email, idn),
            Password.parse(password),
            DisplayName.parse(display_name),
            parse_locale(locale),
            UserTimeZone.parse(time_zone),
        ):
            case (Err(error=rejected), *_):
                return Err(EmailRejected(rejected))

            case (_, Err(error=rejected), *_):
                return Err(PasswordRejected(rejected))

            case (_, _, Err(error=rejected), *_):
                return Err(DisplayNameRejected(rejected))

            case (_, _, _, Err(error=rejected), _):
                return Err(LocaleRejected(rejected))

            case (_, _, _, _, Err(error=rejected)):
                return Err(TimeZoneRejected(rejected))

            case (
                Ok(value=parsed_email),
                Ok(value=parsed_password),
                Ok(value=parsed_display_name),
                Ok(value=parsed_locale),
                Ok(value=parsed_time_zone),
            ):
                return Ok(
                    cls(
                        user_id=UserId.generate(),
                        email=parsed_email,
                        password_hash=await hasher.hash(parsed_password),
                        display_name=parsed_display_name,
                        time_zone=parsed_time_zone,
                        locale=parsed_locale,
                        status=Active(),
                        registered_at=clock.now(),
                        key=_KEY,
                    )
                )

            case _:  # pragma: no cover -- jeder Ausgang ist `Ok` oder `Err`
                msg = "unreachable: ein Result ist entweder Ok oder Err"
                raise AssertionError(msg)

    def __eq__(self, other: object) -> bool:
        """Vergleiche ueber die Identitaet, nicht ueber die Attribute."""
        return isinstance(other, User) and self.id == other.id

    def __hash__(self) -> int:
        """Hashe ueber die Identitaet, passend zu `__eq__`."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Zeige Identitaet und E-Mail - nie den Passwort-Hash."""
        return f"User(id={self.id}, email={self.email.value!r})"
