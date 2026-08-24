# Python Rule Pattern

> Uebersetzt `csharp-rule-pattern.md` sinngemaess. Die
> C#-Vorlage referenziert ein konkretes fremdes Projekt (`DhcpMacVerwaltung`); die Beispiele unten
> bleiben generisch (`Order`, `SwapRequest`).
>
> **Gebaut zu sehen ist beides im Referenz-Slice** `src/contexts/identity`: der gemeinsame
> Collect-all-Typalias in `src/contexts/shared_kernel/validation.py` (`Rule`, `all_of`,
> `FieldError`), seine Anwendung in
> `application/register_user/validators/register_user_rules.py`, und der Fail-fast-Zweig als
> `chain(...)` in `domain/value_objects/email.py` — dort setzt `_RULES: ResultRule[str, EmailError]`
> die einzeln benannten Adressregeln zusammen.

Zwei Bausteine decken jede "ist dieser Input/Zustand gueltig?"-Frage ab — beide sind das
[Rule Pattern](https://dev.to/stevsharp/the-rule-pattern-in-c-2ed0) (eine Regel ist ein Objekt
bzw. hier eine Funktion mit fester Signatur, kein Ad-hoc-`if`), sie unterscheiden sich in der
Fehlerform und darin, wie sie komponiert werden.

## Zwei Varianten, gewaehlt nach Fehlerform — nicht nach Gewohnheit

| | Collect-all Rule | Fail-fast Result Rule |
|---|---|---|
| Fehlerform | viele unabhaengige Feldfehler, gemeinsam berichtet | genau ein typisierter Domaenenfehler |
| Signatur | `Callable[[T], list[FieldError]]` | `Callable[[T], Result[T, E]]` |
| Komposition | `all_of(*rules)` — wertet **alle** Regeln aus, sammelt alle Meldungen | `chain(*rules)` — wertet die naechste Regel nur aus, wenn die vorherige per `.bind` erfolgreich war; erster Fehler gewinnt |
| Typischer Ort | Eingabe-Formatvalidierung an der public Grenze | Domaeneninvarianten (Existenz, Eigentuemerschaft, Kollision) |
| Auswertung je Regel | einmal pro Aufruf — zweimal insgesamt, wenn beide Fragen gestellt werden | genau einmal — der `Result`-Rueckgabewert traegt den Fehler direkt |

Do — Collect-all-Validierung:
```python
type Rule[T] = Callable[[T], list[FieldError]]


def all_of[T](*rules: Rule[T]) -> Rule[T]:
    def combined(value: T) -> list[FieldError]:
        return [error for rule in rules for error in rule(value)]

    return combined


def computer_name_required(request: SwapRequest) -> list[FieldError]:
    if request.computer_name:
        return []
    return [FieldError("computerName", ComputerNameRequired.code, {})]


def scope_id_required(request: SwapRequest) -> list[FieldError]:
    if request.scope_id:
        return []
    return [FieldError("scopeId", ScopeIdRequired.code, {})]


swap_rules: Rule[SwapRequest] = all_of(computer_name_required, scope_id_required)
# swap_rules(request) meldet beide leeren Pflichtfelder auf einmal — nicht nur das erste.
```

**Eine Regel meldet einen Code, nie einen fertigen Satz.** `list[str]` waere hier falsch: der Text
haengt an `Accept-Language` und entsteht erst am HTTP-Rand, waehrend `FieldError` traegt, was
sprachunabhaengig ist — Feldname, Code, Parameter
([python-error-handling.md](./python-error-handling.md), "Die Fehlernutzlast ist ein typisierter
Fall, nie ein fertiger Satz").

**Und eine Regel beantwortet ihre Frage selbst.** Delegiert sie an eine `parse`-Factory, gehoert
die Fallunterscheidung ueber deren Fehler-Union **in die Regel** — nicht in einen generischen
Helfer, dem man den passenden Konverter hereinreicht. Ein solcher Helfer muss seine Signatur ueber
alle Fehlertypen spannen, die er bedient, und wird dabei erst weit (`Result[object, ...]`) und dann
unwahr. Der Preis der ausgeschriebenen Arme ist Laenge; der Preis des Helfers ist eine Annotation,
die nicht mehr stimmt. Gebaut zu sehen in
`application/register_user/validators/register_user_rules.py`, wo `email_must_be_wellformed`
vierzehn Arme hat — einen je Adressregel, jeder mit eigenem Code.

Do — Fail-fast Domaenen-Check mit einem typisierten Fehler:
```python
type ResultRule[T, E] = Callable[[T], Result[T, E]]


def chain[T, E](*rules: ResultRule[T, E]) -> ResultRule[T, E]:
    def combined(value: T) -> Result[T, E]:
        result: Result[T, E] = Ok(value)
        for rule in rules:
            result = result.bind(rule)
        return result

    return combined


# Das `E` gehoert der Operation: hier die Union der Ausgaenge dieser einen Pruefung,
# kein context-weiter Sammeltyp (siehe python-feature-slices.md).
def reservation_exists(server: DhcpServer) -> Result[DhcpServer, ScopeError]: ...
def old_mac_matches(server: DhcpServer) -> Result[DhcpServer, ScopeError]: ...

check = chain(reservation_exists, old_mac_matches)
outcome = check(server)  # genau ein Fehler kommt direkt aus outcome, keine Nachfrage noetig
```

### Don't: Collect-all auf einen Fail-fast-Fall mit einem typisierten Fehler zwingen

```python
def all_of_bool(*rules: Callable[[T], bool]) -> Callable[[T], bool]:
    def combined(value: T) -> bool:
        return all(rule(value) for rule in rules)

    return combined


checks = all_of_bool(old_mac_matches_bool, target_mac_free_bool)
if not checks(reservation):
    if not old_mac_matches_bool(reservation):     # zweite Auswertung — Geruch
        return Err(...)
    return Err(...)
```

Muss eine Regel (oder ihre Bool-Auswertung) nach einem Fehlschlag ein zweites Mal laufen, nur um
herauszufinden, *welche* Regel fehlgeschlagen ist — das ist das Zeichen, dass die falsche
Komposition gewaehlt wurde. `chain`/`Result.bind` existiert genau deshalb: der `Result`-Wert
traegt den einen aufgetretenen Fehler bereits in sich.

### Don't: Ein feature-lokales Duplikat der Rule-`Protocol` nachbauen

```python
class CheckRule(Protocol[T]):        # strukturell identisch zum gemeinsamen Rule/ResultRule-Typ
    def is_satisfied(self, value: T) -> bool: ...
    def messages(self, value: T) -> list[FieldError]: ...
```

Braucht ein Feature "ein Objekt, das entscheidet und begruendet", ist das eine `Rule`/
`ResultRule` aus dem gemeinsamen Modul — nicht eine strukturell gleichgeformte, aber separat
definierte `Protocol`-Klasse daneben. Echte Wiederverwendung heisst, dass der Feature-Code vom
gemeinsamen Typalias abhaengt, nicht dass er ihm nur aehnelt.

## Strukturelle Typisierung ersetzt C#s `in T`-Kontravarianz

In C# muss `IRule<in T>` explizit als kontravariant markiert werden, damit eine Regel gegen ein
gemeinsames Interface fuer mehrere konkrete Request-Typen wiederverwendbar ist. Python braucht
dafuer keine Varianz-Annotation: Eine Regel, die gegen ein schmales `Protocol` geschrieben ist
(nur die Felder, die sie tatsaechlich braucht), passt strukturell auf **jeden** Typ, der dieses
Protocol erfuellt — Duck Typing macht das automatisch.

```python
class SwapQuestion(Protocol):
    computer_name: str
    scope_id: str
    ip_address: str
    old_mac: str
    new_mac: str


# Ein Regelwerk, gueltig fuer jeden Request-Typ, der SwapQuestion erfuellt — ohne Varianz-Syntax:
def validate(request: SwapQuestion) -> list[FieldError]:
    return swap_rules(request)
```

Nur einsetzen, wenn zwei *verschiedene* Request-Typen tatsaechlich dieselbe Validierungsfrage
ueber dieselben Felder stellen (Ausfuehrung vs. Vorschau derselben Operation) — nicht, um
unverwandte Typen in ein gemeinsames Regelwerk zu zwingen, dem sie inhaltlich nicht zustimmen.

## Eine Regel darf warten: `AsyncRule[T]` neben `Rule[T]`

Manche Fragen sind ohne IO nicht zu beantworten — ein Nachschlagen in einer Referenzliste, eine
Rueckfrage bei einem fremden Context ueber einen Port. Als `Rule[T]` sind sie nicht formulierbar
und wandern sonst zwangslaeufig in den Handler, wo sie niemand mehr als Regel wiederfindet. Dafuer
steht neben der synchronen Form dieselbe Form mit Wartezeit:

```python
type AsyncRule[T] = Callable[[T], Awaitable[list[FieldError]]]


def all_of_async[T](*rules: AsyncRule[T]) -> AsyncRule[T]: ...   # alle laufen, alle Meldungen fallen an
def as_async[T](rule: Rule[T]) -> AsyncRule[T]: ...              # hebt eine synchrone Regel
```

Zwei Dinge daran sind Regel, nicht Geschmack:

- **Eine synchrone Regel wird gehoben, nicht `async` umgeschrieben.** `as_async` macht sie
  anschlussfaehig; sie ohne IO als `async def` zu schreiben ist eine Zusage, die sie nicht einloest.
- **Kein Cancellation-Token daneben.** `asyncio` propagiert den Abbruch ueber `CancelledError`
  selbst; `all_of_async` nutzt `asyncio.TaskGroup`, damit unabhaengige Regeln nebenlaeufig laufen
  und der Abbruch an alle durchschlaegt ([python-async.md](./python-async.md)).

## ODER: `any_of`, wenn ein Wert in mehr als einer Form gueltig ist

`chain` bindet — es kann nur UND. Ist ein Wert in mehreren, einander ausschliessenden Formen
gueltig (eine Zeitzone ist eine IANA-Kennung **oder** ein fester UTC-Versatz), ist der Kombinator
`any_of`: der erste Zweig, der `Ok` meldet, gewinnt, die folgenden laufen gar nicht mehr.

```python
def any_of[T, E](first: ResultRule[T, E], *rest: ResultRule[T, E]) -> ResultRule[T, E]: ...


_RULES: ResultRule[str, UserTimeZoneError] = any_of(is_known_time_zone_id, is_fixed_utc_offset)

# Der Kombinator entscheidet nicht, was ein Wert war, der zu keiner Form passt — das tut der Aufrufer:
return _RULES(raw.strip()).map_err(lambda _: UserTimeZoneUnknown(raw)).map(cls)
```

Drei Dinge daran sind Regel, nicht Geschmack:

- **Die Reihenfolge ist eine fachliche Aussage.** Wer zuerst steht, entscheidet, als was ein
  mehrdeutiger Wert gelesen wird (`Etc/GMT-1` ist eine Kennung, kein Versatz).
- **Der ueberlebende Fehler ist keine.** Scheitern alle Zweige, traegt das Ergebnis den Fehler des
  letzten — beliebig. Der Aufrufer uebersetzt ihn per `map_err` in den einen ehrlichen Fall
  („diese Angabe ist keine der beiden Formen"). Kein `sonst`-Parameter am Kombinator: `map_err`
  leistet dasselbe ohne Zwischenschicht.
- **Die erste Regel ist ein eigener Parameter.** ODER hat kein neutrales Element: `all_of()` darf
  mit null Regeln „alles gueltig" bedeuten, `any_of()` haette keinen Fehler zu melden.

Gebaut zu sehen in `domain/value_objects/user_time_zone.py`; die Entscheidung samt verworfener
Alternativen steht in `docs/decisions/2026-08-24-1500-any-of-gebaut-fuer-die-zeitzone.md`.

Der Kombinator **Conditional** aus der Vorlage bleibt bewusst nicht gebaut — eine Regel ist hier
eine Funktion und darf selbst verzweigen (`docs/decisions/2026-08-07-1331-…`).

## Validierungsregeln laufen als erstes Behavior der Pipeline, nicht vorab im Command geparst

Die Collect-all-`Rule` wird direkt gegen das public Request-DTO registriert und vom
**Validierungs-Behavior** der Pipeline konsumiert (`validating(...)` in
`shared_kernel/behaviors/validating.py`; siehe [python-error-handling.md](./python-error-handling.md) fuer den
`Result`-Typ und [python-feature-slices.md](./python-feature-slices.md) fuer die Behavior-Kette).
Es hebt die gesammelten `FieldError` in den **einen** Fehlerkanal des Use Case und kuerzt ab —
nicht ein `if` im Slice, das einen zweiten Kanal und einen zweiten Fold nach sich zoege.

Damit sieht der Kern-Handler nie einen ungueltigen Request, und die Command-Konstruktion, die
daraus die Domaenen-Value-Objects baut, ist **infallibel**: Validierung ist bereits eine Ebene
hoeher gelaufen, das Command braucht deshalb keinen eigenen `Result`/Fehlerkanal, der diese
Pruefung dupliziert.

## Review-Checkliste

- [ ] Fehlerform entscheidet die Variante: viele unabhaengige Feldfehler ⇒ Collect-all-`Rule`; genau ein typisierter Domaenenfehler ⇒ Fail-fast-`ResultRule`. Nie die Komposition der einen Form dem Anwendungsfall der anderen aufzwingen.
- [ ] Eine Regel meldet `FieldError` (Feld, Code, Parameter), nie `list[str]` mit fertigem Text — der Text entsteht erst am HTTP-Rand nach `Accept-Language`.
- [ ] Die Fallunterscheidung ueber die Fehler-Union der `parse`-Factory steht **in der Regel**, nicht in einem generischen Helfer mit Konverter-Callback. Sobald eine Signatur `object`, `Any` oder ein zu weites `Exception` traegt, um mehrere Fehlertypen zu bedienen, ist die Zwischenschicht der Fehler — nicht die Laenge der ausgeschriebenen Arme.
- [ ] Keine Regel wird nach einem Fehlschlag ein zweites Mal ausgewertet, nur um herauszufinden, welche Teilregel fehlgeschlagen ist — diese Information kommt aus der einen Auswertung.
- [ ] Keine feature-lokale `Protocol`-Klasse bildet `Rule`/`ResultRule` strukturell nach; Features importieren/komponieren den gemeinsamen Typalias.
- [ ] Eine ueber mehrere Request-Typen geteilte Regel ist dadurch gerechtfertigt, dass sie wirklich dieselbe Frage ueber dieselben Felder stellt, ausgedrueckt ueber ein gemeinsames `Protocol` — nicht durch das Zusammenzwingen unverwandter Typen.
- [ ] Validierung laeuft als **erstes Behavior** der Pipeline via `Rule[TRequest]`/`AsyncRule[TRequest]`, nicht als `if` im Slice und nicht vorab im Command geparst; die Command-Konstruktion ist infallibel, sobald Validierung vorgelagert bereits gelaufen ist.
- [ ] Eine Regel ist nur dann `AsyncRule`, wenn sie wirklich IO braucht; eine synchrone Regel wird mit `as_async` gehoben, nicht umgeschrieben.
- [ ] Ein Wert, der in mehreren einander ausschliessenden Formen gueltig ist, wird mit `any_of` ausgedrueckt, nicht mit einer `if`-Kette — und der Fall „keine der Formen" kommt per `map_err` vom Aufrufer, nicht vom Kombinator.
- [ ] **Jede** Pruefung steht als benannte Funktion und wird als `_RULE`/`_RULES` deklariert — auch die einzelne. `parse` verdrahtet nur noch (`_RULES(raw).map(cls)`); ein `if` oder ein `try` im Rumpf von `parse` ist der Befund.
- [ ] Wandelt die Pruefung den Typ (`str -> UUID`, `str -> Locale`), ist sie eine `ParseRule[TIn, TOut, E]` — **trotzdem eine Regel**, nur keine verkettbare: `chain`/`any_of` setzen gleiche Ein- und Ausgangsform voraus, verkettet wird per `.bind`.
- [ ] Kein `raw.strip()` neben den Regeln. Trimmen ist die erste Regel der Kette (`not_blank` aus `shared_kernel/text_rules.py`), nicht eine Vorbereitung davor — sonst sieht jede folgende Regel einen Wert, den sie erneut anfassen muesste.
