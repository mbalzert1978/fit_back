# Python Rule Pattern

> Uebersetzt `csharp-rule-pattern.md` sinngemaess. Die
> C#-Vorlage referenziert ein konkretes fremdes Projekt (`DhcpMacVerwaltung`) — hier stattdessen
> generisch anhand eines Platzhalter-Beispiels (`Order`). Wird ein Referenz-Feature in diesem
> Projekt etabliert, diese Datei darauf aktualisieren.

Zwei Bausteine decken jede "ist dieser Input/Zustand gueltig?"-Frage ab — beide sind das
[Rule Pattern](https://dev.to/stevsharp/the-rule-pattern-in-c-2ed0) (eine Regel ist ein Objekt
bzw. hier eine Funktion mit fester Signatur, kein Ad-hoc-`if`), sie unterscheiden sich in der
Fehlerform und darin, wie sie komponiert werden.

## Zwei Varianten, gewaehlt nach Fehlerform — nicht nach Gewohnheit

| | Collect-all Rule | Fail-fast Result Rule |
|---|---|---|
| Fehlerform | viele unabhaengige Feldfehler, gemeinsam berichtet | genau ein typisierter Domaenenfehler |
| Signatur | `Callable[[T], list[str]]` | `Callable[[T], Result[T, E]]` |
| Komposition | `all_of(*rules)` — wertet **alle** Regeln aus, sammelt alle Meldungen | `chain(*rules)` — wertet die naechste Regel nur aus, wenn die vorherige per `.bind` erfolgreich war; erster Fehler gewinnt |
| Typischer Ort | Eingabe-Formatvalidierung an der public Grenze | Domaeneninvarianten (Existenz, Eigentuemerschaft, Kollision) |
| Auswertung je Regel | einmal pro Aufruf — zweimal insgesamt, wenn beide Fragen gestellt werden | genau einmal — der `Result`-Rueckgabewert traegt den Fehler direkt |

Do — Collect-all-Validierung:
```python
type Rule[T] = Callable[[T], list[str]]


def all_of[T](*rules: Rule[T]) -> Rule[T]:
    def combined(value: T) -> list[str]:
        return [message for rule in rules for message in rule(value)]

    return combined


def computer_name_required(request: SwapRequest) -> list[str]:
    return [] if request.computer_name else ["computer_name is required"]


def scope_id_required(request: SwapRequest) -> list[str]:
    return [] if request.scope_id else ["scope_id is required"]


swap_rules: Rule[SwapRequest] = all_of(computer_name_required, scope_id_required)
# swap_rules(request) meldet beide leeren Pflichtfelder auf einmal — nicht nur das erste.
```

Do — Fail-fast Domaenen-Check mit einem typisierten Fehler:
```python
type ResultRule[T] = Callable[[T], "Result[T, DomainError]"]


def chain[T](*rules: ResultRule[T]) -> ResultRule[T]:
    def combined(value: T) -> "Result[T, DomainError]":
        result: Result[T, DomainError] = Ok(value)
        for rule in rules:
            result = result.bind(rule)
        return result

    return combined


def reservation_exists(server: DhcpServer) -> "Result[DhcpServer, DomainError]": ...
def old_mac_matches(server: DhcpServer) -> "Result[DhcpServer, DomainError]": ...

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
    def messages(self, value: T) -> list[str]: ...
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
def validate(request: SwapQuestion) -> list[str]:
    return swap_rules(request)
```

Nur einsetzen, wenn zwei *verschiedene* Request-Typen tatsaechlich dieselbe Validierungsfrage
ueber dieselben Felder stellen (Ausfuehrung vs. Vorschau derselben Operation) — nicht, um
unverwandte Typen in ein gemeinsames Regelwerk zu zwingen, dem sie inhaltlich nicht zustimmen.

## Validierungsregeln laufen in der Handler-Pipeline, nicht vorab im Command geparst

Die Collect-all-`Rule` wird direkt gegen das public Request-DTO registriert und von einem
Validierungs-Decorator (siehe [python-error-handling.md](./python-error-handling.md) fuer den
`Result`-Typ und [python-feature-slices.md](./python-feature-slices.md) fuer die
Handler-Pipeline) konsumiert — der Kern-Handler sieht nie einen ungueltigen Request, und die
Command-Konstruktion, die daraus die Domaenen-Value-Objects baut, ist **infallibel**: Validierung
ist bereits eine Ebene hoeher gelaufen, das Command braucht deshalb keinen eigenen
`Result`/Fehlerkanal, der diese Pruefung dupliziert.

## Review-Checkliste

- [ ] Fehlerform entscheidet die Variante: viele unabhaengige Feldfehler ⇒ Collect-all-`Rule`; genau ein typisierter Domaenenfehler ⇒ Fail-fast-`ResultRule`. Nie die Komposition der einen Form dem Anwendungsfall der anderen aufzwingen.
- [ ] Keine Regel wird nach einem Fehlschlag ein zweites Mal ausgewertet, nur um herauszufinden, welche Teilregel fehlgeschlagen ist — diese Information kommt aus der einen Auswertung.
- [ ] Keine feature-lokale `Protocol`-Klasse bildet `Rule`/`ResultRule` strukturell nach; Features importieren/komponieren den gemeinsamen Typalias.
- [ ] Eine ueber mehrere Request-Typen geteilte Regel ist dadurch gerechtfertigt, dass sie wirklich dieselbe Frage ueber dieselben Felder stellt, ausgedrueckt ueber ein gemeinsames `Protocol` — nicht durch das Zusammenzwingen unverwandter Typen.
- [ ] Validierung laeuft in der Pipeline via `Rule[TRequest]`, nicht vorab im Command geparst; die Command-Konstruktion ist infallibel, sobald Validierung vorgelagert bereits gelaufen ist.
