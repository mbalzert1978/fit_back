# Python Null Safety

> Uebersetzt `csharp-null-safety.md` sinngemaess. "Null Safety"
> heisst hier: `None` ist immer explizit im Typ sichtbar (`ANN`-Regeln erzwingen die Annotation),
> nie stillschweigend moeglich.

## Guards nur an public Grenzen, nicht in privaten Funktionen

Validiere/guard nur an public Einstiegspunkten (Modul-Level-Funktionen ohne `_`-Praefix, public
Methoden). Private Funktionen (`_`-Praefix) setzen gueltigen, bereits geprueften Zustand voraus —
kein redundanter Guard dort.

Do:
```python
def process_order(order: Order | None) -> None:  # public Grenze
    if order is None:
        raise ValueError("order must not be None")
    _validate_internal(order)


def _validate_internal(order: Order) -> None:  # kein Null-Check, order ist hier garantiert gueltig
    ...
```

Don't:
```python
def _validate_internal(order: Order | None) -> None:
    if order is None:               # redundant in privater Funktion
        raise ValueError("order must not be None")
```

## Fehlermeldungen referenzieren den echten Namen

Python hat kein `nameof()`. Der Parametername in der Fehlermeldung ist ein String-Literal — halte
Signatur und Meldung im selben Funktionskoerper, damit ein Rename beim naechsten Edit sofort
auffaellt, statt in getrennten Dateien zu verwaisen.

Do:
```python
def process_order(order: Order | None) -> None:
    if order is None:
        raise ValueError("order must not be None")
    logger.warning("field %s is invalid", "order.total")
```

Don't:
```python
def process_order(order: Order | None) -> None:
    if order is None:
        raise ValueError("value must not be None")  # sagt nicht, welcher Parameter
```

## Explizite Nullability

`None`-faehige Felder/Parameter immer explizit als `X | None` annotieren — nie implizit durch
einen Default von `None` ohne Typannotation. Fuer Narrowing an nicht-trivialen Stellen
`TypeGuard`/`TypeIs` (aus `typing`) einsetzen, statt `assert`-Ketten ohne Typaussage.

Do:
```python
@dataclass(slots=True)
class OrderProcessor:
    logger: Logger | None = None
```

Don't:
```python
@dataclass(slots=True)
class OrderProcessor:
    logger=None  # kein Typ, keine ANN-Konformitaet, Nullability unsichtbar
```
