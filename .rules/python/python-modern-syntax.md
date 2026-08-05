# Python Modern Syntax

> Uebersetzt `csharp-modern-syntax.md` sinngemaess. Zwei
> Abschnitte des Originals (Sonar-Analyzer-Placement-Quirk bei Extension Blocks, XML-Doc-Cref-
> Aufloesung) sind reine Roslyn-/Sonar-/XML-Doc-Compiler-Eigenheiten ohne Entsprechung im
> Python-Toolstack (kein Extension-Methods-Sprachfeature, keine XML-Doc-Kompilierung, kein
> Sphinx/Doc-Tool im Einsatz) — sie werden hier bewusst **nicht** miteruebersetzt statt geraten.
> Falls spaeter ein Doc-Generator (z. B. Sphinx mit `nitpicky`-Cross-Referencing) eingefuehrt
> wird, an dieser Stelle nachtragen.

## f-Strings statt `%`-Formatierung oder `.format()`

Do:
```python
message = f"Field {field_name} is invalid"
```

Don't:
```python
message = "Field %s is invalid" % field_name
message = "Field {} is invalid".format(field_name)
```

## Pattern Matching statt verschachtelter `if`/`isinstance`-Ketten

Siehe [python-control-flow.md](./python-control-flow.md) fuer die volle Regel inkl.
Exhaustivitaets-Fallback.

## PEP-695-Generics statt `typing.Generic`/`TypeVar`/`TypeAlias`

`requires-python = ">=3.14"` schaltet die native Generics-Syntax (PEP 695, seit 3.12) frei. Jeder
generische Typalias und jede generische Klasse/Funktion nutzt sie — kein `TypeVar`-Import, kein
`Generic[...]`-Basisklasse, kein `TypeAlias`-Import mehr noetig.

Do:
```python
class Ok[T]:
    value: T


def first[T](items: Sequence[T]) -> T:
    return items[0]


type Result[T, E] = Ok[T] | Err[E]
```

Don't:
```python
T = TypeVar("T")


class Ok(Generic[T]):
    value: T


def first(items: Sequence[T]) -> T:  # ungebundenes Modul-T statt eigenem Typparameter
    return items[0]


Result: TypeAlias = Ok[T] | Err[E]  # TypeAlias-Import ueberfluessig ab 3.12
```

## Walrus-Operator gezielt, nicht inflationaer

`:=` nutzen, um eine Zuweisung und ihre unmittelbare Pruefung zusammenzuziehen — nicht, um
mehrere unabhaengige Zuweisungen in einen Ausdruck zu quetschen.

Do:
```python
if (match := pattern.search(line)) is not None:
    process(match)
```

Don't:
```python
if (a := compute_a()) and (b := compute_b()) and (c := a + b) > threshold:  # unlesbar
    ...
```

## Sortierbare IDs: `uuid.uuid7()` statt `uuid.uuid4()`

Generiere IDs mit `uuid.uuid7()` (stdlib ab Python 3.14, per `requires-python = ">=3.14"` in
`pyproject.toml` verfuegbar), nie `uuid.uuid4()`, wenn die ID in einem Index landet. Version-7-
UUIDs betten einen Zeitstempel ein und sortieren chronologisch, sodass sequenzielle Inserts die
Index-Lokalitaet behalten statt zufaellige v4-Werte ueber den B-Tree zu streuen.

Do:
```python
order_id = OrderId(uuid.uuid7())
```

Don't:
```python
order_id = OrderId(uuid.uuid4())  # zufaellige v4 — fragmentiert Index-Inserts
```

## Lint-Ausnahmen: `# noqa: CODE -- Begruendung`, nie blank oder dateiweit

Muss eine ruff-Regel im Einzelfall unterdrueckt werden, geschieht das inline mit Regelcode **und**
Begruendung nach `--` an genau der betroffenen Zeile — nie ein nacktes `# noqa`, das alle Regeln
unterdrueckt, und nie ein dateiweites `# ruff: noqa` ohne Scope. Der Kommentar ist verortet,
verschwindet mit der Zeile beim Refactoring und zwingt zu einer sichtbaren Begruendung.

Do:
```python
result = eval(expression)  # noqa: S307 -- expression stammt aus einer statischen, versionierten Konfigdatei
```

Don't:
```python
result = eval(expression)  # noqa  -- unterdrueckt jede Regel, nicht nur die gemeinte
```
```python
# ruff: noqa
# irgendwo am Dateianfang — unterdrueckt die ganze Datei ohne Begruendung
```
