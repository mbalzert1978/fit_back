# Python Control Flow

> Uebersetzt `csharp-control-flow.md` sinngemaess.

## Pattern Matching statt if/elif- und `isinstance`-Ketten

Bevorzuge `match`/`case` (PEP 634) gegenueber langen `if`/`elif`-Ketten. Es ist kompakter und
komponierbar.

**Die Regel gilt fuer zwei Formen, nicht nur fuer eine.** Die zweite ist die haeufigere und wurde
lange uebersehen, weil die Ueberschrift nur die erste nannte: eine von Hand geschriebene
Struktur-Pruefung aus verschachtelten `if` plus `isinstance` plus Attributvergleich. Genau dafuer
ist `case` da — die Form steht im Muster, die Bedingung im Guard.

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

### Die zweite Form: verschachtelte `isinstance`-Pruefungen

Aus `tests/test_architecture_datetime.py`, wo ein AST nach `datetime.now()` ohne `tz`-Argument
durchsucht wird. Die alte Fassung hatte kognitive Komplexitaet **46** bei einer Schwelle von 15.

Don't:
```python
if isinstance(node, ast.Call):
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "now"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "datetime"
    ):
        has_tzinfo = False
        for keyword in node.keywords:
            if keyword.arg in ("tz", "tzinfo"):
                has_tzinfo = True
                break
        if not has_tzinfo:
            errors.append(...)
```

Do:
```python
match node:
    case ast.Call(
        lineno=int() as line,
        func=ast.Attribute(attr="now", value=ast.Name(id="datetime")),
        keywords=keywords,
    ) if not any(keyword.arg in _TZ_KEYWORDS for keyword in keywords):
        yield line, "datetime.now() ohne tz-Argument - nutze TimeProvider.utc_now()"
```

Vier `isinstance`, zwei Attributvergleiche und eine Flag-Schleife werden ein `case`. Das Muster
beschreibt die **Form**, der Guard die **Bedingung**, und die Zeilennummer faellt beim Zerlegen
gleich mit ab.

## Sammeln als Ausdruck, nicht als Akkumulator

Eine leere Liste, eine Schleife mit `.append()`, danach `if liste: ...` — das ist dieselbe
Handarbeit wie eine `isinstance`-Kette, nur fuer Daten statt fuer Verzweigungen.

Der Abschnitt „Collection-Literale statt Aufbau per Schleife" weiter unten deckt diesen Fall
**nicht** ab: er gilt nur, wenn die Werte im Voraus bekannt sind. Gerade wenn sie es nicht sind,
gehoert das Sammeln in einen Generator oder eine Comprehension.

Don't:
```python
errors: list[tuple[Path, int, str]] = []
for py_file in root.rglob("*.py"):
    for node in ast.walk(ast.parse(py_file.read_text())):
        if _ist_befund(node):
            errors.append((py_file, node.lineno, "..."))

if errors:
    msg = "Verletzung:\n"
    for file_path, line_no, error_msg in errors:
        msg += f"  {file_path}:{line_no}: {error_msg}\n"
    raise AssertionError(msg)
```

Do:
```python
def _befunde(tree: ast.Module) -> Iterator[tuple[int, str]]:
    """Jede Fundstelle des Moduls."""
    ...


_kein_befund(
    (
        _Befund(py_file, line, reason)
        for py_file, tree in _modules(keep)
        for line, reason in _befunde(tree)
    ),
    "Verletzung:",
)
```

Drei Dinge fallen dabei weg: die veraenderliche Liste, die zweite Schleife fuer die Meldung, und
die Wiederholung des Ganzen im naechsten Test. Wie die Fundstelle aussieht, weiss `_Befund.__str__`
— an genau einer Stelle.

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
