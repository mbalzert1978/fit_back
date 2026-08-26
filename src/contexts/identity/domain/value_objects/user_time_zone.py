"""Value Object UserTimeZone - IANA-Zone oder fester UTC-Versatz."""

from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from typing import Final, Self, final
from zoneinfo import available_timezones

from src.contexts.identity.domain.user_time_zone_errors import (
    UserTimeZoneError,
    UserTimeZoneIsEmpty,
    UserTimeZoneUnknown,
)
from src.contexts.shared_kernel import (
    ConstructionKey,
    Err,
    Ok,
    Result,
    deny_foreign_key,
    not_blank_as,
)
from src.contexts.shared_kernel.validation import ResultRule, any_of, chain

__all__ = ["DEFAULT_TIME_ZONE_ID", "UserTimeZone"]

DEFAULT_TIME_ZONE_ID = "Europe/Berlin"
"""Default laut BACKEND.md Abschnitt 1."""

_OFFSET_PREFIXES = ("UTC", "GMT")
"""Praefixe, die derselben Zone vorangestellt sein duerfen.

`GMT+01:00` kommt aus einer der beiden 201-Interaktionen des Frontend-Vertrags
und ist **keine** IANA-Zone - gemessen gegen `zoneinfo.available_timezones()`.
Der Vertrag gewinnt, die Invariante wird nachgezogen
(`docs/decisions/2026-08-21-2200-vertrag-zieht-anzeigename-und-zeitzone-nach.md`).

Genau **eines** davon faellt weg, nicht beide nacheinander: sonst waere auch
`UTCGMT+01:00` eine Zeitzone.
"""

_SIGN_AND_HOURS: Final = slice(3)
"""`+01` aus der kompakten Form `+0100`."""

_MINUTES: Final = slice(3, 5)
"""`00` aus der kompakten Form `+0100`."""


@final
@dataclass(frozen=True, slots=True)
class _NotThisForm:
    """Dieser Zweig ist es nicht - mehr sagt eine der beiden Formregeln nicht.

    Ein formloser Marker statt eines fertigen `UserTimeZoneUnknown`: welcher
    Fehler nach aussen geht, entscheidet erst `has_a_known_form`, wenn **keine**
    Form gepasst hat. Baute ihn schon der Zweig, entstuende bei jedem Aufruf eine
    Nutzlast, die der Aufrufer sofort wieder wegwirft.
    """


_NOT_THIS_FORM = _NotThisForm()


@cache
def _known_time_zone_ids() -> frozenset[str]:
    """Lies die IANA-Kennungen einmal ein - `available_timezones` scannt jedes Mal neu."""
    return frozenset(available_timezones())


def _without_offset_prefix(raw: str) -> str:
    """Entferne genau das eine Praefix, das vorne steht - kein zweites danach."""
    return next(
        (raw.removeprefix(prefix) for prefix in _OFFSET_PREFIXES if raw.startswith(prefix)),
        raw,
    )


def _normalized_offset(raw: str) -> str | None:
    """Bringe einen festen Versatz auf die eine Form `±HH:MM`, sonst None.

    Genau eine Schreibweise geht in den Bestand: sonst waeren `GMT+01:00`,
    `+0100` und `+01:00` drei Werte fuer dieselbe Zone, und jeder Vergleich
    darauf muesste sie erst wieder zusammenfuehren.

    Geparst wird mit `strptime("%z")` statt mit einer eigenen Regex: das ist
    dieselbe ISO-8601-Auslegung, die CPython auch fuer `datetime` benutzt, und
    sie weist einen Versatz jenseits von ±24 Stunden von sich aus zurueck.
    """
    try:
        parsed = datetime.strptime(_without_offset_prefix(raw), "%z")
    except ValueError:
        return None
    compact = parsed.strftime("%z")
    return f"{compact[_SIGN_AND_HOURS]}:{compact[_MINUTES]}"


is_not_blank: ResultRule[str, UserTimeZoneError] = not_blank_as(UserTimeZoneIsEmpty)
"""Die Angabe besteht nicht nur aus Leerraum - und kommt getrimmt zurueck."""


def is_known_time_zone_id(candidate: str) -> Result[str, _NotThisForm]:
    """Die Angabe ist eine IANA-Kennung.

    Erster Zweig: `Etc/GMT-1` ist eine Kennung und kein Versatz - und soll es
    bleiben.
    """
    if candidate in _known_time_zone_ids():
        return Ok(candidate)
    return Err(_NOT_THIS_FORM)


def is_fixed_utc_offset(candidate: str) -> Result[str, _NotThisForm]:
    """Die Angabe ist ein fester UTC-Versatz - normalisiert auf `±HH:MM`."""
    if (offset := _normalized_offset(candidate)) is None:
        return Err(_NOT_THIS_FORM)
    return Ok(offset)


_FORMS: ResultRule[str, _NotThisForm] = any_of(is_known_time_zone_id, is_fixed_utc_offset)


def has_a_known_form(candidate: str) -> Result[str, UserTimeZoneError]:
    """Die Angabe ist eine der beiden gueltigen Formen - Kennung oder Versatz.

    Ein Fall statt je Zweig einer: `+25:00` ist weder das eine noch das andere,
    und "keine IANA-Kennung" waere davon die willkuerlich herausgegriffene
    Haelfte
    (`docs/decisions/2026-08-24-1730-leerer-wert-ist-ein-eigener-fehlerfall.md`).
    Hier - und nur hier - entsteht deshalb die eine `UserTimeZoneUnknown`.
    """
    return _FORMS(candidate).map_err(lambda _: UserTimeZoneUnknown(candidate))


_RULES: ResultRule[str, UserTimeZoneError] = chain(is_not_blank, has_a_known_form)

_KEY: Final = ConstructionKey()
"""Der modul-private Schluessel - nur `parse` und `hydrate` unten haben ihn."""


@final
@dataclass(frozen=True, slots=True)
class UserTimeZone:
    """Die Zone, in der die Tagebuch-Tage des Users liegen.

    Zwei Formen, und nur diese zwei: eine bekannte IANA-Kennung
    (`Europe/Berlin`) oder ein fester Versatz gegen UTC (`+01:00`). Wer den Wert
    in eine `tzinfo` verwandelt, muss beide behandeln - `ZoneInfo` kennt den
    Versatz nicht, `datetime.timezone` kennt die Sommerzeit nicht.
    """

    value: str
    key: ConstructionKey = field(repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        """Weise jeden Bau ab, der nicht durch `parse` oder `hydrate` ging."""
        deny_foreign_key(self.key, _KEY)

    @classmethod
    def parse(cls, raw: str) -> Result[Self, UserTimeZoneError]:
        """Pruefe eine Zeitzonen-Angabe gegen die IANA-Datenbank oder als festen Versatz."""
        return _RULES(raw).map(lambda checked: cls(checked, key=_KEY))

    @classmethod
    def hydrate(cls, raw: str) -> UserTimeZone:
        """Rekonstruiere aus einem bereits validierten Rohwert."""
        match cls.parse(raw):
            case Ok(value=time_zone):
                return time_zone
            case Err():
                msg = f"unreachable: {raw!r} wurde vorgelagert validiert"
                raise AssertionError(msg)
