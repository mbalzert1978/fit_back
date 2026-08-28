"""Zugangsdaten - was der Nutzer bei der Aufnahme mitbekommt.

Gebaut werden sie von der Wurzel selbst (`User.issue_credentials`), nicht von
einem Adapter zusammengesetzt. Deshalb stehen sie in der Domaene: sie sind das
Ergebnis einer Aggregat-Operation und nicht der Rueckgabetyp einer Naht
(docs/decisions/2026-08-28-1045-die-wurzel-stellt-ihre-zugangsdaten-aus.md).

Der Refresh-Token steht hier im **Klartext** und wird nie abgelegt; abgelegt
wird das Aggregat `RefreshToken` mit seinem Abdruck.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Final, Self, final

from src.contexts.identity.domain.value_objects.token_lifetime import TokenLifetime
from src.contexts.shared_kernel import ConstructionKey, deny_foreign_key

__all__ = ["Grant", "IssuedCredentials"]

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `hydrate` unten hat ihn."""


@final
@dataclass(frozen=True, slots=True)
class Grant:
    """Ein ausgegebener Token und wie lange er gilt.

    Die beiden gehoeren zusammen: ein Token ohne seine Geltungsdauer ist fuer den
    Aufrufer unbrauchbar, eine Dauer ohne Token gegenstandslos. Vorher lagen sie
    als vier lose Felder nebeneinander, und nichts hielt das eine Paar vom
    anderen fern.

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

        Ein Eliminator wie `Result.fold`, aus demselben Grund: der Aufrufer sagt,
        was er bauen will, statt sich die Teile einzeln herauszunehmen. Er kennt
        damit weder `TokenLifetime` noch die Namen der Felder hier drin
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

    def fold[T](self, present: Callable[[str, int, str, int], T], /) -> T:
        """Gib beide Ausgaben heraus - Access zuerst, Refresh danach.

        Der Aufrufer bekommt vier Primitive gereicht und greift nirgends hinein.
        Ohne diesen Weg stuende beim Response-Mapper viermal eine Kette wie
        `credentials.access.lifetime.seconds` - drei Glieder tief durch zwei
        fremde Objekte
        (docs/decisions/2026-08-28-1120-die-zugangsdaten-geben-heraus-was-sie-wissen.md).
        """
        return self.access.fold(
            lambda token, seconds: self.refresh.fold(partial(present, token, seconds))
        )
