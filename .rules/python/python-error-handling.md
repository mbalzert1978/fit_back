# Python Error Handling

> Uebersetzt `csharp-error-handling.md` sinngemaess. Python
> ist kulturell staerker EAFP-gepraegt als C# — die hier uebersetzte Regel schraenkt das bewusst
> ein: EAFP ist gut fuer *wirklich* seltene/unerwartete Faelle, nicht als Ersatz fuer erwartete
> Kontrollfluss-Entscheidungen.

## Sentinel-Rueckgaben statt Exceptions fuer erwartete Faelle

Nutze `dict.get(key, default)`, `key in dict`, `str.removeprefix`/`removesuffix` u. ae. fuer
Operationen, deren "Nicht-Erfolg" ein normales Kontrollfluss-Ergebnis ist. Exceptions bleiben fuer
wirklich unerwartete Fehler reserviert.

Do:
```python
if (order := orders.get(key)) is not None:
    process_order(order)

if (quantity := try_parse_int(text)) is not None:
    process_quantity(quantity)
```

Don't:
```python
try:
    order = orders[key]  # wirft bei fehlendem Key
    process_order(order)
except KeyError:
    pass  # erwarteter Fall — dict.get() waere die richtige Wahl
```

Exceptions signalisieren Bugs oder wirklich unerwartete Laufzeitfehler, nicht wiederkehrende
Alternativen.

## Async: keine Exception als Kontrollfluss

Don't:
```python
async def get_order(order_id: str) -> Order:
    order = await repository.find(order_id)
    if order is None:
        raise NotFoundError(order_id)  # erwarteter Fall — Aufrufer muesste fangen
    return order
```

Do:
```python
async def get_order(order_id: str) -> "OrderResult":
    order = await repository.find(order_id)
    return Found(order) if order is not None else NotFound(order_id)


@dataclass(frozen=True, slots=True)
class Found:
    order: Order


@dataclass(frozen=True, slots=True)
class NotFound:
    order_id: str


type OrderResult = Found | NotFound
```

## Ein gemeinsamer `Result[T, E]` fuer die binaere "Wert oder Fehlschlag"-Form — feature-lokale Tagged Unions fuer echte Algebren

Jeder Ausgang der Form "Erfolg mit einem Wert, oder Fehlschlag mit einer Nutzlast" — unabhaengig
davon, ob die Nutzlast ein `str` oder ein eigener Fehlertyp ist — ist ein gemeinsamer
`Result[T, E]`, keine feature-lokale Zwei-Fall-Union. Das deckt Value-Object-Parsing
(`Mac.parse(...)`, `ScopeId.parse(...)` → `Result[Mac, str]`) genauso ab wie "gefunden oder mit
der nicht getroffenen Anfrage fehlgeschlagen" (`Result[MacMatch, ScopeId]` — der Fehlerfall traegt
die angefragte `ScopeId` als typisierte Daten, nicht als Text). Das gilt **nicht** fuer einen
Ausgang mit mehr als zwei, unabhaengig geformten *Erfolgs*faellen (eine echte Domaenenalgebra) —
das bleibt eine feature-lokale Tagged Union, wie jede andere geschlossene Wertemenge
([python-types.md](./python-types.md)).

Do:
```python
def parse(raw: str) -> "Result[Mac, str]": ...
def check(server: DhcpServer, ...) -> "Result[Reservation, DomainError]": ...
```

Don't:
```python
# Zwei-Fall-Union, die nur Result[T, E] neu erfindet
@dataclass(frozen=True, slots=True)
class MacParseOk:
    value: Mac


@dataclass(frozen=True, slots=True)
class MacParseError:
    message: str


type MacParseResult = MacParseOk | MacParseError  # die x-te Kopie derselben Form
```

**`Result[T, E]` implementiert man einmal, generisch, ohne neue Dependency** — ueber PEP-695-
native Generics (`class Ok[T]:`, `type Result[T, E] = ...`; kein `typing.Generic`/`TypeVar`/
`TypeAlias`-Import noetig, siehe [python-modern-syntax.md](./python-modern-syntax.md)), nicht pro
Feature neu:

```python
@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T

    def map[U](self, f: Callable[[T], U]) -> "Result[U, E]":
        return Ok(f(self.value))

    def bind[U, E](self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return f(self.value)


@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

    def map[T, U](self, f: Callable[[T], U]) -> "Err[E]":
        return self

    def bind[T, U](self, f: Callable[[T], "Result[U, E]"]) -> "Err[E]":
        return self


type Result[T, E] = Ok[T] | Err[E]
```

`Err.map`/`Err.bind` deklarieren ihren Rueckgabetyp als `Err[E]`, nicht als `Result[U, E]`: `Err[E]`
ist fuer jedes `U` bereits ein gueltiges `Result[U, E]` (die Union haengt im `Err`-Zweig gar nicht
von `U` ab), das `self` zurueckgeben ist also strukturell korrekt. Deshalb braucht es **kein**
`# type: ignore` — so ein Kommentar waere ohnehin wirkungslos, da dieser Stack bewusst ohne
mypy/pyright auskommt (siehe oben) und ihn nie jemand auswertet.

`match` ist der uebliche Weg, ein `Result` zu entpacken — nicht ein manuelles `isinstance`-Paar:

```python
match outcome:
    case Ok(value=order):
        ...
    case Err(error=reason):
        ...
```

## Zwei Factories je Value Object: fallibles `parse` vs. infallibles `hydrate`

Ein Value Object, dessen Gueltigkeit nicht strukturell durch seinen Typ garantiert ist (eine
IP-Adresse, eine MAC-Adresse, jedes weitere feature-eigene VO um ein rohes Format), bekommt
**zwei** Erzeugungswege — nie nur `parse`:

- **`parse(raw: str) -> Result[T, E]`** — der fallible Einstiegspunkt fuer einen Wert, der
  tatsaechlich fehlerhaft sein koennte: Nutzereingabe, ein Request-DTO-Feld, alles, was eine
  Vertrauensgrenze ueberquert.
- **`hydrate(raw: str) -> T`** — infallible Rekonstruktion fuer einen Wert, dessen Format bereits
  bekannt-gueltig ist: entweder weil ein `parse`-gestuetzter Validierungsschritt schon frueher in
  derselben Pipeline gelaufen ist, oder weil der Rohwert aus einer vertrauenswuerdigen internen
  Quelle stammt (ein Repository, das Entitaeten aus bereits validierten Persistenzdaten
  rekonstruiert). `hydrate` ruft intern `parse` auf und entpackt per `match`; der theoretisch
  unmoegliche Fehlerfall wird zu `raise AssertionError("unreachable")` — `hydrate` implementiert
  die Validierung nicht neu.

Ein Fehlschlag innerhalb von `hydrate` ist ein Programmierfehler (falsche vorgelagerte Annahme),
nie ein erwarteter Ausgang — genau deshalb wirft es, statt einen `Result` zurueckzugeben.

Do:
```python
def parse(raw: str) -> "Result[Mac, str]":
    if not _MAC_PATTERN.match(raw):
        return Err(f"invalid mac address: {raw}")
    return Ok(Mac(raw))


def hydrate(raw: str) -> Mac:
    match parse(raw):
        case Ok(value=mac):
            return mac
        case Err():
            raise AssertionError(f"unreachable: {raw} was validated upstream")
```

Don't:
```python
def hydrate(raw: str) -> Mac:
    # Formatpruefung neu implementiert statt an parse zu delegieren
    if not _MAC_PATTERN.match(raw):
        raise AssertionError("unreachable")
    return Mac(raw)
```

## Nur an der IO-Naht fangen — sonst fail fast

`try`/`except` lebt an genau einer Stelle: im IO-/Infrastruktur-Adapter hinter einem Port, dessen
Vertrag "das kann fehlschlagen" ueber einen `Result`-Rueckgabetyp erklaert. Ueberall sonst —
Handler, Prozessoren, Domaenenobjekte — faengt der Code nie; eine unerwartete Exception propagiert
und das Programm scheitert laut.

Do:
```python
class ConsumerFileSystem(Protocol):
    async def rename(self, source: str, destination: str) -> "RenameResult": ...


class ConsumerFileSystemAdapter:
    async def rename(self, source: str, destination: str) -> "RenameResult":
        try:
            await asyncio.to_thread(os.rename, source, destination)
            return RenameOk()
        except OSError as error:
            return RenameFailed(str(error))


# Domaene matcht auf das Result — sie faengt nie:
async def reveal(fs: ConsumerFileSystem, tmp: str, final: str) -> "RevealOutcome":
    match await fs.rename(tmp, final):
        case RenameFailed(reason=reason):
            return Faulted(reason)
        case RenameOk():
            return Revealed()
```

Don't:
```python
async def reveal(fs: ConsumerFileSystem, tmp: str, final: str) -> "RevealOutcome":
    try:
        ...
    except Exception as error:  # noqa: BLE001 -- verschluckt unerwartete Bugs als Domaenen-Fehlschlag
        return Faulted(str(error))
```

Ist ein Port **nicht** als fallibel deklariert, wird nicht gefangen — er darf werfen. Einen
unerwarteten Fehler als `Failed`-Result zu maskieren versteckt Bugs.
