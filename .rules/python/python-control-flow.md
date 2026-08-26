# Python Control Flow

> Uebersetzt `csharp-control-flow.md` sinngemaess.

## Pattern Matching statt if/elif-Ketten

Bevorzuge `match`/`case` (PEP 634) gegenueber langen `if`/`elif`-Ketten. Es ist kompakter und
komponierbar.

Do:
```python
def calculate_discount(customer: Customer) -> float:
    match customer:
        case Customer(tier=CustomerTier.PREMIUM):
            return 0.2
        case Customer(order_count=count) if count > 10:
            return 0.1
        case _:
            return 0.0
```

Don't:
```python
def calculate_discount(customer: Customer) -> float:
    if customer.tier == CustomerTier.PREMIUM:
        return 0.2
    if customer.order_count > 10:
        return 0.1
    return 0.0
```

## Exhaustive Matches ueber geschlossene Unions

Fuer `match` ueber eine geschlossene Menge von Varianten (`Union`/`|` aus `@dataclass`-Typen,
oder `Enum`) immer einen werfenden Abschlusszweig `case _: assert_never(<subjekt>)` — nie ein
`case _: ...`, das den unbekannten Fall still ignoriert. Die volle Regel — warum es genau
`typing.assert_never` ist und kein selbstgebautes `raise`, wie mit fremden Fallmengen umzugehen ist
und wie das maschinell abgesichert wird — steht in
[python-error-handling.md](./python-error-handling.md) („Jeder `match` ist vollstaendig") und gilt
dort wie hier, ohne Ausnahme.

Python hat **keine** Compile-Zeit-Exhaustivitaetspruefung ohne Typchecker. `ty` prueft `match`
gegen eine Union, meldet aber in diesem Repo an mehreren Stellen noch falsch (siehe die
`type-assertion-failure`-Baseline in `pyproject.toml`). Der werfende Arm bleibt deshalb der
**verlaessliche** Schutz: eine neue
Variante scheitert **laut zur Laufzeit**, nicht beim Linten. Das ist dieselbe Garantie wie C#s
`_ => throw new UnreachableException()` unter `TreatWarningsAsErrors` — dort erzwingt der
Compiler den Arm, hier erzwingt ihn Konvention plus Tests.

Liste bekannte Faelle explizit auf (eigene `case`-Zeilen oder `|`-Alternativen), damit `case _`
wirklich nur echte neue Varianten faengt — nie als Sammelbecken fuer Faelle, die man sich nicht
extra aufgeschrieben hat.

Do:
```python
def to_context(state: SyncFileState | None) -> DownloadContext | None:
    match state:
        case SyncFileState.Discovered(size=size):
            return DownloadContext(size)
        case SyncFileState.Downloaded() | SyncFileState.Grouped():
            return None  # bereits ueber Discovered hinaus — no-op
        case None:
            return None
        case _:
            assert_never(state)
```

Don't:
```python
def to_context(state: SyncFileState | None) -> DownloadContext | None:
    match state:
        case SyncFileState.Discovered(size=size):
            return DownloadContext(size)
        case _:
            return None  # verschluckt None UND jede zukuenftige Variante
```

## Slicing statt manueller Indexlogik oder Iterator-Ketten

Nutze Python-Slicing statt `list(...)`-Umwege oder manuelle Schleifen fuer einfache Ausschnitte.

Do:
```python
last = items[-1]
first_three = items[:3]
middle = items[2:5]
```

Don't:
```python
last = items[len(items) - 1]
first_three = [item for i, item in enumerate(items) if i < 3]
```

## Collection-Literale statt Aufbau per Schleife

Wenn die Werte im Voraus bekannt sind, direkt als Literal schreiben statt Schritt fuer Schritt
per `.append()` aufzubauen.

Do:
```python
fruits: list[str] = ["Apple", "Banana", "Cherry"]
```

Don't:
```python
fruits: list[str] = []
fruits.append("Apple")
fruits.append("Banana")
fruits.append("Cherry")
```
