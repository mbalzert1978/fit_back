"""Zugangsdaten - was der Nutzer bei der Aufnahme mitbekommt.

Jede Haelfte wird von der Domaene ausgestellt: der Refresh-Grant von
`RefreshToken.issue`, der Access-Grant vom Port `AccessTokens`. Gepaart werden
sie vom Handler, der die Ausstellung fuehrt
(docs/decisions/2026-08-28-1450-der-handler-orchestriert-die-ausstellung.md).

Der Refresh-Token steht hier im **Klartext** und wird nie abgelegt; abgelegt
wird das Aggregat `RefreshToken` mit seinem Abdruck.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Final, Protocol, Self, final

from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["CredentialsPresenter", "Grant", "IssuedCredentials"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur die `hydrate` unten haben ihn."""


class CredentialsPresenter[T](Protocol):
    """Was aus zwei Ausgaben gebaut werden soll - der Empfaenger von `IssuedCredentials.fold`.

    Die vier Werte sind keyword-only; vertauschen laesst sie sich damit nicht
    (docs/decisions/2026-08-28-1450-der-handler-orchestriert-die-ausstellung.md).
    """

    def __call__(
        self,
        *,
        access_token: str,
        expires_in: int,
        refresh_token: str,
        refresh_expires_in: int,
    ) -> T:
        """Baue das Ergebnis aus den vier benannten Werten."""
        ...


@final
@dataclass(frozen=True, slots=True)
class Grant:
    """Ein ausgegebener Token und wie lange er gilt.

    Die beiden gehoeren zusammen: ein Token ohne seine Geltungsdauer ist fuer den
    Aufrufer unbrauchbar, eine Dauer ohne Token gegenstandslos.

    `token` traegt `repr=False`: er ist ein Geheimnis wie ein Passwort und hat in
    keinem Log etwas zu suchen.
    """

    token: str = field(repr=False)
    lifetime: TokenLifetime
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(cls, token: str, lifetime: TokenLifetime) -> Self:
        """Paare den ausgegebenen Token mit der Dauer, fuer die er gilt."""
        return cls(token, lifetime, key=_KEY)

    def fold[T](self, present: Callable[[str, int], T], /) -> T:
        """Gib Token und Sekunden heraus - was daraus wird, entscheidet der Aufrufer.

        Ein Eliminator wie `Result.fold`
        (docs/decisions/2026-08-26-1130-result-fold-als-eliminator.md).
        """
        return present(self.token, self.lifetime.seconds)


@final
@dataclass(frozen=True, slots=True)
class IssuedCredentials:
    """Der Zugang und das Recht, ihn zu erneuern.

    Zwei Ausgaben und keine vier Felder: `access` und `refresh` sind
    verschiedene Dinge mit verschiedenen Lebensdauern - der eine wird signiert
    und weggeworfen, der andere hat ein Aggregat hinter sich (`RefreshToken`).
    """

    access: Grant
    refresh: Grant
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def hydrate(cls, access: Grant, refresh: Grant) -> Self:
        """Paare die beiden Ausgaben, die dieselbe Ausstellung hergegeben hat."""
        return cls(access, refresh, key=_KEY)

    def fold[T](self, present: CredentialsPresenter[T], /) -> T:
        """Gib beide Ausgaben benannt heraus - der Aufrufer greift nirgends hinein.

        Derselbe Eliminator wie bei `Grant`
        (docs/decisions/2026-08-28-1120-die-zugangsdaten-geben-heraus-was-sie-wissen.md).
        """
        return self.access.fold(
            lambda access_token, expires_in: self.refresh.fold(
                lambda refresh_token, refresh_expires_in: present(
                    access_token=access_token,
                    expires_in=expires_in,
                    refresh_token=refresh_token,
                    refresh_expires_in=refresh_expires_in,
                )
            )
        )
