"""Die Sperre gegen den rohen Konstruktor eines Value Object."""

from typing import final

__all__ = ["ConstructionKey", "deny_foreign_key"]


@final
class ConstructionKey:
    """Der Beleg, dass ein Value Object durch seine eigene Factory gebaut wurde.

    Jedes Value-Object-Modul haelt genau eine Instanz davon, modul-privat. Wer von
    aussen konstruieren will, hat sie nicht - und der Konstruktor weist ihn ab.
    Damit ist "nur ueber `parse` oder `hydrate`" keine Bitte in einer Docstring
    mehr, sondern eine Sperre, die auch der haelt, der die Docstring nicht liest.

    Eine eigene Klasse und kein `object()`: so steht in der Signatur des Feldes,
    wofuer der Wert da ist, und ein versehentlich durchgereichtes `None` faellt
    schon dem Typpruefer auf statt erst zur Laufzeit.
    """

    __slots__ = ()


def deny_foreign_key(actual: ConstructionKey, expected: ConstructionKey) -> None:
    """Weise jeden Bau ab, der nicht durch die Factory des eigenen Moduls ging.

    `AssertionError` und kein `Result`: ein roher Konstruktoraufruf ist ein
    Programmierfehler, kein erwarteter Fachfall - und ein Fehlerkanal dafuer
    stuende in jeder Signatur, die den Wert nur weiterreicht
    (.rules/python/python-error-handling.md).
    """
    if actual is expected:
        return
    msg = "unreachable: nur ueber die Factory des eigenen Moduls zu bauen"
    raise AssertionError(msg)
