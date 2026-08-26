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
davon, wie die Nutzlast geformt ist — ist ein gemeinsamer
`Result[T, E]`, keine feature-lokale Zwei-Fall-Union. Das deckt Value-Object-Parsing
(`Mac.parse(...)`, `ScopeId.parse(...)` → `Result[Mac, MacError]`) genauso ab wie "gefunden oder mit
der nicht getroffenen Anfrage fehlgeschlagen" (`Result[MacMatch, ScopeId]` — der Fehlerfall traegt
die angefragte `ScopeId` als typisierte Daten, nicht als Text). Das gilt **nicht** fuer einen
Ausgang mit mehr als zwei, unabhaengig geformten *Erfolgs*faellen (eine echte Domaenenalgebra) —
das bleibt eine feature-lokale Tagged Union, wie jede andere geschlossene Wertemenge
([python-types.md](./python-types.md)).

**Ausgenommen ist die public Naht eines Use Case.** Ihr Ergebnis ist eine eigene, einfache Tagged
Union aus Primitiven — nie `Result[T, E]`, auch wenn sie genau zwei Faelle hat: der `Result` ist der
Domaenen-Fehlerkanal und bleibt domaenenseitig
([python-feature-slices.md](./python-feature-slices.md), „Die Naht gehoert dem Use Case"). Betreten
wird der `Result` erst im Port-Adapter, der die Naht-Union per `match` nach
`Result[T, <Port>Error]` uebersetzt (siehe „Verketten oder matchen" weiter unten).

Do:
```python
def parse(raw: str) -> "Result[Mac, MacError]": ...
def check(server: DhcpServer, ...) -> "Result[Reservation, ReservationError]": ...
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

    def fold[U, E](self, on_ok: Callable[[T], U], _on_err: Callable[[E], U], /) -> U:
        return on_ok(self.value)


@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

    def map[T, U](self, f: Callable[[T], U]) -> "Err[E]":
        return self

    def bind[T, U](self, f: Callable[[T], "Result[U, E]"]) -> "Err[E]":
        return self

    def fold[T, U](self, _on_ok: Callable[[T], U], on_err: Callable[[E], U], /) -> U:
        return on_err(self.error)


type Result[T, E] = Ok[T] | Err[E]
```

`Err.map`/`Err.bind` deklarieren ihren Rueckgabetyp als `Err[E]`, nicht als `Result[U, E]`: `Err[E]`
ist fuer jedes `U` bereits ein gueltiges `Result[U, E]` (die Union haengt im `Err`-Zweig gar nicht
von `U` ab), das `self` zurueckgeben ist also strukturell korrekt. Deshalb braucht es **kein**
`# type: ignore`. Der Typechecker dieses Stacks ist `ty`; wo er hier trotzdem meldet, steht die
Ausnahme als benannte Baseline in `pyproject.toml` statt als Kommentar im Code.

**`fold` ist der Weg aus dem `Result` heraus, nicht `match`.** `map`, `bind`, `map_err` und
`or_else` bleiben im `Result`; `fold` ist die eine Operation, die kontrolliert herausfuehrt — der
**Eliminator**. Er nimmt je einen Arm fuer beide Ausgaenge und liefert einen Wert:

```python
return outcome.fold(_accepted, _rejected)
```

Der `Ok`/`Err`-Split steht damit **einmal** in `result.py` statt an jeder Fundstelle. Ein manuelles
`isinstance`-Paar ist an dieser Stelle ohnehin falsch; ein `match` ueber `Ok`/`Err` ist es seit dem
Eliminator ebenso (siehe „Damit `ty` die Zusage einloesen kann" weiter unten und
[`2026-08-26-1130`](../../docs/decisions/2026-08-26-1130-result-fold-als-eliminator.md)).

## Die Fehlernutzlast ist ein typisierter Fall, nie ein fertiger Satz

Das `E` in `Result[T, E]` sagt, **was** der Fall ist — nicht, **wie er heisst**. Jeder Fehlschlag,
dessen Formulierung je einen Menschen erreichen kann, ist ein eigener `@final
@dataclass(frozen=True, slots=True)`-Fall mit typisierter Nutzlast, zusammengefasst zu einer
geschlossenen Union ([python-types.md](./python-types.md)). Ein `str` als `E` ist an dieser Stelle
ein Regelverstoss.

Do:
```python
@final
@dataclass(frozen=True, slots=True)
class PasswordTooShort:
    actual_length: int
    minimum: int


@final
@dataclass(frozen=True, slots=True)
class PasswordHasNoDigit: ...


type PasswordError = PasswordTooShort | PasswordHasNoDigit


@classmethod
def parse(cls, raw: str) -> "Result[Password, PasswordError]":
    if len(raw) < MINIMUM_LENGTH:
        return Err(PasswordTooShort(len(raw), MINIMUM_LENGTH))
    return Ok(cls(raw))
```

Don't:
```python
@classmethod
def parse(cls, raw: str) -> "Result[Password, str]":
    # Die Sprache ist damit dort entschieden, wo niemand weiss, wer fragt -
    # und die 10 ist aus dem Satz nicht mehr herauszuholen.
    return Err(f"Passwort muss mindestens {MINIMUM_LENGTH} Zeichen lang sein")
```

Vier Dinge haengen daran:

1. **Die Sprache wird spaet entschieden.** Der Text entsteht erst, wo bekannt ist, wer fragt — am
   HTTP-Rand mit dem `Accept-Language`-Header in der Hand. Eine Domaene, die Saetze zurueckgibt,
   ist einsprachig, egal welche Middleware davorsteht.
2. **Die Vollstaendigkeit wird bewacht.** Der `match` ohne Auffangzweig, der den Fall formuliert,
   meldet beim naechsten neuen Fall, dass die Meldung dafuer fehlt
   ([python-control-flow.md](./python-control-flow.md)). Ueber Strings kann das niemand pruefen.
3. **Die Nutzlast ueberlebt bis zur Formulierung.** Das `{minimum}` einer Textvorlage wird aus dem
   Fehlerwert gefuellt, nicht aus einem Satz rekonstruiert. Deutsch und Englisch duerfen die Zahl
   verschieden platzieren, ohne dass die Domaene davon weiss.
4. **Der Fall wird der stabile Vertrag.** Der Klassenname ist der Fehlercode, `title`/`detail` sind
   Kosmetik darueber. Ein umformulierter Satz ist damit keine API-Aenderung mehr.

Die Nutzlast traegt genau das, was die Formulierung braucht (Maximum, ungueltige Zeichen, den
Rohwert) — nichts, das niemand liest, und nichts, das der Aufrufer nach aussen nie preisgeben darf.

**Abgrenzung.** Ein `str` bleibt richtig, wo die Zeichenkette **Diagnose** ist und nie zu einer
Nutzermeldung wird: die `OSError`-Meldung im IO-Adapter (`RenameFailed(str(error))` weiter unten),
Log-Text, der Grund eines Infrastruktur-Fehlschlags. Faustregel: erreicht die Formulierung je eine
Antwort an einen Aufrufer, ist sie ein typisierter Fall.

**Verketten, falten oder matchen — die Grenze verlaeuft am Container.** Drei Faelle, und jeder hat
genau ein Werkzeug:

- Bleibt der Ausgang ein `Result` und aendert sich nur der Fehlertyp, wird **verkettet**:
  `Email.parse(raw, idn).map_err(to_field_fault)`.
- Wird der `Result` **verlassen** (in eine Response-Union, in eine `FieldError`-Liste), wird
  **gefaltet**: `outcome.fold(_accepted, _rejected)`. Nicht gematcht — ein `match` ueber `Ok`/`Err`
  ist genau die Stufe, die der Eliminator abnimmt.
- Wird der `Result` aus einer fremden Union heraus **betreten** (Naht-Ergebnis →
  `Result[T, <Port>Error]` im Port-Adapter, z. B. `Result[User, UserRegistryError]`), wird
  **gematcht** — dort gibt es kein `Err`, auf dem eine Kette oder ein Fold sitzen koennte.

Der Wachposten geht dabei nicht verloren, er zieht nur um: er sitzt jetzt **im Fehler-Arm des
Folds**, der flach ueber die Fehler-Union matcht und mit `assert_never` schliesst. Kommt ein Fall
dazu, bricht er dort laut auf, waehrend eine Kette aus zwei Funktionen ihn still durchreichen wuerde
([python-control-flow.md](./python-control-flow.md)). Damit er das wirklich tut, braucht er den
werfenden Abschlusszweig aus dem naechsten Abschnitt — **ohne** ihn bricht er gerade nicht auf.

**Ueber die Naht des Use Case gehen weiterhin nur Primitive**
([python-feature-slices.md](./python-feature-slices.md)). Die Domaenen-Union endet also an der
Application-Grenze; dort wird sie in Code plus Parameter uebersetzt, nicht in einen Satz.
Referenz im Repo: `contexts/identity/domain/email_errors.py` und der `EmailError`-`match`, der sie
auswertet.

## Jeder `match` ist vollstaendig — der Abschlusszweig wirft `assert_never`

**Ein `match` endet nie offen.** Der letzte Zweig faengt entweder einen echten Restfall ab oder
wirft; ein `match`, der beides nicht tut, ist ein Fehler, kein Stil.

Der Grund ist eine Eigenschaft der Sprache, die man leicht falsch erinnert: **Python erzwingt
Vollzaehligkeit zur Laufzeit nicht.** Passt kein Zweig, faellt der `match` still durch — in einer
Funktion mit Rueckgabewert heisst das `None`, und der Fehler taucht irgendwo weiter oben als
`AttributeError` auf einem `NoneType` auf, weit weg von seiner Ursache. In C# meldet das der
Compiler; hier meldet es `ty` — aber nur, wo die Fallmenge geschlossen ist und die Einengung
im Muster ankommt. Ein aufgezaehlter `match` "ohne Auffangzweig" ist deshalb **kein**
Wachposten — er ist die Luecke.

Der Abschluss ist [`typing.assert_never`](https://docs.python.org/3/library/typing.html#typing.assert_never),
das Gegenstueck zu C#s `_ => throw new UnreachableException()`:

```python
from typing import assert_never

def locale_tag(locale: Locale) -> str:
    match locale:
        case German():
            return "de"
        case English():
            return "en"
        case _:
            assert_never(locale)
```

`assert_never` ist der stdlib-Weg und traegt doppelt: zur Laufzeit wirft es einen `AssertionError`
mit dem unerwarteten Wert, und `ty` meldet einen nicht behandelten Fall schon beim Pruefen statt
erst im Betrieb. Ein selbstgebauter `raise RuntimeError("unreachable")` kann das zweite nicht.

**Damit `ty` die Zusage einloesen kann, matcht der Code flach ueber die Fehler-Union** — nie
verschachtelt im `Err`. Steht der Fehlerfall im Muster (`case Err(error=EmailIsEmpty())`), traegt
`ty` die Einengung nicht ins Typargument von `Err` hinein; der Restfall bleibt `Err[EmailError]`
statt `Never`, und `assert_never` ist wieder nur Laufzeitschutz. Ueber einer flachen Union rechnet
`ty` die Vollzaehligkeit dagegen aus.

**Den `Ok`/`Err`-Split nimmt `fold` ab, nicht eine zweite `match`-Stufe.** Der Fehler-Arm bekommt
den Fehlerwert bereits ausgepackt und matcht flach darueber:

```python
def to_response(outcome: Result[Registration, RegisterUserError]) -> RegisterUserResponse:
    return outcome.fold(_accepted, _rejected)


def _rejected(error: RegisterUserError) -> RegisterUserResponse:
    match error:
        case RequestInvalid(errors=errors):
            return RegistrationInvalid(group_by_field(errors))
        case EmailAlreadyRegistered(email=email):
            return EmailAlreadyTaken(email.value)
        case _:
            assert_never(error)
```

Ein `match` ueber `Ok`/`Err` mit einem zweiten `match` darin ist damit **abgeloest**: er kostete
zwei `assert_never` je Funktion und eine Einrueckungsebene, ohne mehr zuzusichern
([`2026-08-26-1130`](../../docs/decisions/2026-08-26-1130-result-fold-als-eliminator.md)).

**Immer `assert_never`, auch wo der Rest nicht streng `Never` ist.** Es gibt Faelle, die typmaessig
gueltig sind und trotzdem nie ankommen, weil eine Stufe davor sie ausschliesst — `to_response` im
`register_user`-Slice sieht keinen `PasswordTooShort`, weil die Pipeline vorher validiert. Fuer
solche Stellen liegt eine eigene, sprechend benannte Ausnahme nahe ("diese Annahme ist gebrochen"
statt "unerwarteter Wert").

Das ist bewusst **nicht** die Regel hier. `assert_never` ist zur Laufzeit nichts anderes als
`raise AssertionError(f"... but got: {value!r}")` — eine eigene Klasse daneben ist dieselbe
Mechanik unter anderem Namen und kauft nur eine Sonderregel ein, die jeder Leser und jedes Review
erst auseinanderhalten muss. Der Wert steht in beiden Meldungen; damit ist auch bei einem
"ausgeschlossenen" Fall sofort sichtbar, welcher durchgerutscht ist. Ein Zweig, ein Muster, keine
Abwaegung an der Schreibstelle.

**Das Subjekt muss ein Name sein.** `assert_never` braucht den gematchten Wert; ein
`match await pipeline.run(request):` gibt ihn nicht her. Der Name wird deshalb **im Subjekt
gebunden** — zugewiesen und unmittelbar geprueft ist genau der Fall, in dem `:=` Pflicht ist
([python-modern-syntax.md](./python-modern-syntax.md)); eine freistehende Zuweisung davor stuende
nur da, um in der naechsten Zeile geprueft zu werden:

```python
match outcome := await pipeline.run(request):
    ...
    case _:
        assert_never(outcome)
```

**Auch bei fremden Fallmengen — keine Ausnahme.** Naheliegender Einwand: matcht der Code auf eine
**offene Wertemenge aus fremder Hand** (ein Fehlertyp-String von Pydantic, ein Statuscode), sei ein
neuer Fall doch ein Bibliotheks-Update und kein Programmierfehler; ein beantworteter Auffangzweig
sei dort freundlicher als ein Absturz.

Der Einwand traegt nicht. **Eine Aenderung, die niemand adressiert hat, ist ebenso ein Bruch** — ob
sie aus unserem Code kommt oder aus einer Abhaengigkeit, aendert daran nichts. Und der freundliche
Auffangzweig ist nicht freundlich, er luegt: im Repo bildete er `model_attributes_type` (der Body
ist ein Array statt eines Objekts) auf `field-type-error` ab, und der Aufrufer las **"Das Feld ''
muss ein Text sein"** — mit leerem Feldnamen, weil es gar kein Feld gibt. Der Zweig hat den Fehler
nicht abgefedert, sondern verdeckt.

**Der Einwand, der richtig bleibt:** `assert_never` wirkt erst zur Anfragezeit — der Bruch traefe
einen Nutzer, nicht das Deployment. Das ist zu spaet, also gehoert zu einer fremden Fallmenge eine
Pruefung davor:

```python
# Startup: existieren die Faelle, die wir behandeln, in der installierten Version noch?
def verify_pydantic_contract() -> None:
    if verschwunden := sorted(HANDLED_PYDANTIC_ERROR_TYPES - set(get_args(ErrorType))):
        raise ValueError(...)
```

Dazu ein Vertragstest, der die Fallmenge **misst** statt sie zu behaupten — und zwar auf dem Weg,
den die Produktion nimmt. Das ist nicht dasselbe wie die Bibliothek direkt zu fahren: dieselbe
Eingabe meldet ueber FastAPIs Body-Validierung `model_attributes_type`, gegen das Modell allein
`model_type`. Wer die Naht umgeht, misst einen Vertrag, den der Code nie sieht.

Damit greift es dreifach: der Test meldet in der CI, was sich am **Verhalten** aendert, der Start
meldet, was gar nicht mehr **existiert**, und `assert_never` ist die letzte Instanz dahinter statt
der ersten. Referenz im Repo: `src/api/pydantic_contract_check.py` und
`tests/api/test_pydantic_error_contract.py`.

**Maschinell geprueft, nicht erinnert.** `tests/test_match_exhaustiveness.py` liest `src/` per AST
und laesst jeden `match` durchfallen, dessen letzter Zweig weder wirft noch `assert_never` aufruft —
ohne Ausnahmeliste, denn es gibt keine Ausnahme
([`exp_maschinelle-absicherung-statt-review-regel.md`](../../docs/reflections/exp_maschinelle-absicherung-statt-review-regel.md)).

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
def parse(raw: str) -> "Result[Mac, MacError]":
    if not _MAC_PATTERN.match(raw):
        return Err(MacMalformed(raw))
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
