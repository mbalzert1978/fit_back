"""Die Sperre gegen den rohen Konstruktor eines Value Object."""

from typing import final

__all__ = ["ConstructionKey", "deny_foreign_key"]


@final
class ConstructionKey:
    """Der Beleg, dass ein Typ durch die Factory seines eigenen Moduls gebaut wurde.

    Jedes Modul, dessen Typ eine Regel ueber einem Rohwert haelt, legt genau eine
    Instanz davon an, modul-privat. Wer von aussen konstruieren will, hat sie
    nicht - und der Konstruktor weist ihn ab
    (docs/decisions/2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md).

    Eine Tagged Union ohne Rohwert - `Locale`, `AccountStatus` - hat keine solche
    Regel und traegt deshalb keinen Schluessel.
    """

    __slots__ = ()


def deny_foreign_key(actual: ConstructionKey, expected: ConstructionKey) -> None:
    """Weise jeden Bau ab, der nicht durch die Factory des eigenen Moduls ging.

    `AssertionError` und kein `Result`: ein roher Konstruktoraufruf ist ein
    Programmierfehler, kein erwarteter Fachfall
    (.rules/python/python-error-handling.md).
    """
    if actual is expected:
        return
    msg = "unreachable: nur ueber die Factory des eigenen Moduls zu bauen"
    raise AssertionError(msg)
