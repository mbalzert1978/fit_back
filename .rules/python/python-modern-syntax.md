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

## Walrus-Operator: bei "zuweisen und sofort pruefen" ist er Pflicht, sonst zurueckhaltend

Steht eine Zuweisung nur da, um in der **naechsten** Zeile geprueft zu werden, gehoert sie in die
Pruefung hinein. Der Name existiert dann genau dort, wo er gebraucht wird, und niemand kann ihn
spaeter versehentlich weiterverwenden.

Diese Regel hat zwei Haelften, und die zweite wurde lange als die einzige gelesen: `:=` **muss**
stehen, wo zugewiesen und unmittelbar geprueft wird — und es darf **nicht** mehrere unabhaengige
Zuweisungen in einen Ausdruck quetschen. ruff hat dafuer keine Regel; das faellt nur im Review auf.

Do:
```python
if (match := pattern.search(line)) is not None:
    process(match)

if missing := expected - available:
    raise ValueError(f"fehlt: {sorted(missing)}")
```

Don't:
```python
missing = expected - available  # existiert nur fuer die naechste Zeile
if missing:
    raise ValueError(f"fehlt: {sorted(missing)}")
```

Don't:
```python
if (a := compute_a()) and (b := compute_b()) and (c := a + b) > threshold:  # unlesbar
    ...
```

## Ersatzwert per `or`, nicht per nachgeschobenem `if`

Soll ein leerer Wert durch einen Ersatz abgeloest werden, ist das ein Ausdruck, keine
Fallunterscheidung. `x or fallback` sagt es in einer Zeile; die `if`-Variante verteilt dieselbe
Aussage auf vier und laesst die Variable zwischendurch in einem Zustand, den niemand wollte.

ruff faengt nur die Ternary-Form (`FURB110`), nicht die mit `if`-Statement — die faellt im Review
auf.

Do:
```python
args = get_args(union) or (union,)
errors = collected or None
```

Don't:
```python
args = get_args(union)
if not args:
    args = (union,)

errors = collected if collected else None  # dieselbe Aussage, umstaendlicher
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
