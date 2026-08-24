# Deklarative Validierung mit Spec und Result

Anleitung zum Ersetzen imperativer Guard Clauses durch komponierbare
Spezifikationen. Fail-fast, Early Return bleibt erhalten — nur nicht mehr als
Kontrollfluss, sondern als Wert.

Zielversion: **Python 3.14**. Konkret genutzt werden PEP 695 (`class Ok[T]`,
`type`-Alias), PEP 696 (Typparameter-Defaults) und PEP 649/749 — Annotationen
werden verzoegert ausgewertet, Forward References brauchen also keine
Anfuehrungszeichen mehr und kein `from __future__ import annotations`.

---

## Ausgangslage

Imperativ, das `if` steht in jeder Parse-Methode erneut:

```python
@classmethod
def parse(cls, raw: str) -> Result[Password, PasswordError]:
    if len(raw) < MINIMUM_LENGTH:
        return Err(PasswordTooShort(len(raw), MINIMUM_LENGTH))
    if len(raw) > MAXIMUM_LENGTH:
        return Err(PasswordTooLong(len(raw), MAXIMUM_LENGTH))
    return Ok(cls(raw))
```

Ziel: `parse` enthaelt keine Logik mehr, sondern verdrahtet nur noch. Die
fachliche Aussage steht in einer einzigen deklarativen Zeile.

---

## Schritt 1 — Result

Minimale Basis. Wichtig sind `bind` (monadischer Bind, fail-fast) und `map`.

```python
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T

    def bind[U, E](self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return f(self.value)

    def map[U](self, f: Callable[[T], U]) -> Ok[U]:
        return Ok(f(self.value))


@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

    def bind[U, T](self, f: Callable[[T], Result[U, E]]) -> Err[E]:
        return self

    def map[U, T](self, f: Callable[[T], U]) -> Err[E]:
        return self


type Result[T, E] = Ok[T] | Err[E]
```

Drei Dinge, die sich gegenueber der klassischen Schreibweise aendern:

- Keine `TypeVar`-Deklarationen und kein `Generic[T]` mehr — die Typparameter
  stehen direkt an Klasse und Methode und sind sauber gescoped.
- `Result` ist ein echter `type`-Alias, kein Modulattribut. Er ist lazy, darf
  also `Ok` und `Err` referenzieren und gleichzeitig in deren Methoden
  vorkommen.
- `Callable` kommt aus `collections.abc`; die Variante in `typing` ist seit
  3.9 deprecated.

`Err.bind` ignoriert die Funktion — das *ist* der Early Return. Ab hier muss
ihn niemand mehr von Hand schreiben.

---

## Schritt 2 — Spec

Eine Spezifikation ist eine Funktion `T -> Result[T, E]`, verpackt in einen
Wert, damit sie komponierbar wird.

```python
@dataclass(frozen=True, slots=True)
class Spec[T, E]:
    run: Callable[[T], Result[T, E]]

    def __and__(self, other: Spec[T, E]) -> Spec[T, E]:
        return Spec(lambda v: self.run(v).bind(other.run))

    def __call__(self, value: T) -> Result[T, E]:
        return self.run(value)
```

`__and__` verkettet ueber `bind`: greift die linke Spec, wird die rechte nie
ausgefuehrt.

**Algebra:** `&` ist assoziativ, neutrales Element ist `Spec(Ok)`. Damit ist
`Spec` ein Monoid — beliebig viele Regeln, beliebig geklammert, gleiches
Ergebnis.

---

## Schritt 3 — rule

Die einzige Stelle im gesamten Entwurf, an der noch ein `if` steht:

```python
def rule[T, E](pred: Callable[[T], bool], err: Callable[[T], E]) -> Spec[T, E]:
    return Spec(lambda v: Ok(v) if pred(v) else Err(err(v)))
```

Der Fehler wird als **Factory** uebergeben, nicht als Wert. Grund: Fehler
brauchen meist den geprueften Wert (`len(s)`), und im Erfolgsfall soll gar
kein Fehlerobjekt konstruiert werden.

---

## Schritt 4 — Regelvokabular

Benannte, parametrisierte, wiederverwendbare Regeln. Das ist die Ebene, auf
der die Fachsprache entsteht. Mit PEP 696 laesst sich der Fehlertyp einmal
vorbelegen, damit die Signaturen kurz bleiben:

```python
import re

type StrSpec[E = PasswordError] = Spec[str, E]


def min_length(n: int) -> StrSpec:
    return rule(lambda s: len(s) >= n, lambda s: PasswordTooShort(len(s), n))


def max_length(n: int) -> StrSpec:
    return rule(lambda s: len(s) <= n, lambda s: PasswordTooLong(len(s), n))


def matches[E](pattern: str, err_type: Callable[[str], E]) -> StrSpec[E]:
    compiled = re.compile(pattern)
    return rule(lambda s: bool(compiled.fullmatch(s)), err_type)
```

---

## Schritt 5 — Deklaration

```python
class Password:
    SPEC = min_length(MINIMUM_LENGTH) & max_length(MAXIMUM_LENGTH)

    @classmethod
    def parse(cls, raw: str) -> Result[Password, PasswordError]:
        return cls.SPEC(raw).map(cls)
```

`parse` ist jetzt logikfrei. Neue Regel = `& regel(...)` an die `SPEC`-Zeile,
`parse` bleibt unberuehrt.

Der Rueckgabetyp nennt `Password` innerhalb von `Password` — unter PEP 649
ist das ohne Anfuehrungszeichen gueltig, weil die Annotation erst bei Zugriff
ausgewertet wird.

`.map(cls)` steht bewusst am Ende: vorher fliesst der rohe `str` durch, sonst
muesste ein potenziell ungueltiges `Password` konstruiert werden, um es
anschliessend zu pruefen.

---

## Bausteine fuer den Ausbau

### Dynamische Komposition

```python
import operator
from functools import reduce


def all_of[T, E](*specs: Spec[T, E]) -> Spec[T, E]:
    return reduce(operator.and_, specs, Spec(Ok))
```

Nutzt das neutrale Element — funktioniert auch mit null Regeln.

### Policy statt Konstanten

```python
@dataclass(frozen=True, slots=True)
class PasswordPolicy:
    minimum: int
    maximum: int

    @property
    def spec(self) -> StrSpec:
        return min_length(self.minimum) & max_length(self.maximum)


@classmethod
def parse(cls, raw: str, policy: PasswordPolicy = DEFAULT_POLICY) -> Result[Password, PasswordError]:
    return policy.spec(raw).map(cls)
```

Policy wird injizierbar und testbar, ohne dass `parse` sie kennt.

### Felder zusammengesetzter Objekte

```python
def at[T, F, E](field: str, spec: Spec[F, E]) -> Spec[T, E]:
    return Spec(lambda obj: spec.run(getattr(obj, field)).map(lambda _: obj))


USER_SPEC = at("password", Password.SPEC) & at("email", Email.SPEC)
```

Das `.map(lambda _: obj)` gibt das aeussere Objekt zurueck, damit die Spec
weiterhin `T -> Result[T, E]` erfuellt und kettbar bleibt.

### Regeln mit I/O

Eine Regel, die selbst scheitern kann, ist einfach eine `Spec` ohne `rule`:

```python
def not_breached(client: BreachClient) -> StrSpec:
    return Spec(client.check)   # str -> Result[str, PasswordError]


SPEC = min_length(8) & max_length(64) & not_breached(client)
```

Weder `&` noch `parse` aendern sich. Reine und unreine Regeln zu trennen
bleibt trotzdem sinnvoll — siehe unten.

### Auspacken am Rand

`match` ist die einzige Stelle, an der das Result wieder aufgebrochen wird —
idealerweise nur an der Systemgrenze:

```python
match Password.parse(raw):
    case Ok(value=password):
        store(password)
    case Err(error=PasswordTooShort(actual=n)):
        report(f"nur {n} Zeichen")
    case Err(error=e):
        report(str(e))
```

Dass `Ok` und `Err` frozen Dataclasses sind, macht sie direkt
pattern-matchbar; mit `__match_args__` bzw. positionalen Patterns geht auch
`case Ok(password):`.

---

## Wann dieses Muster *nicht* passt

| Situation | Besser |
| --- | --- |
| Zwei triviale Pruefungen, kein Ausbau geplant | Guard Clauses behalten |
| Alle Verstoesse sollen gleichzeitig gemeldet werden | Applicative-Variante: `check: T -> tuple[E, ...]`, `&` konkateniert statt bindet |
| Constraints reichen auf Typebene | Pydantic `Annotated[str, StringConstraints(...)]` |
| Fehler sind unerwartet, nicht Teil der Domaene | Exceptions |

Fail-fast versus Sammeln ist eine bewusste Entscheidung: Bind kann prinzipiell
nicht sammeln. Wer beides braucht, definiert zwei Operatoren — `&` sammelnd,
`>>` bindend — und mischt sie je nach Abhaengigkeit der Regeln.

---

## Checkliste

- [ ] `Result` als `type`-Alias, `Ok`/`Err` mit PEP-695-Typparametern
- [ ] `bind` und `map` vorhanden, `Err` kurzschliessend
- [ ] `Spec` als Wert, `__and__` ueber `bind`
- [ ] `rule` als einzige Stelle mit `if`
- [ ] Fehler als Factory `T -> E`, nicht als Wert
- [ ] Regeln benannt und parametrisiert, nicht als Inline-Lambda
- [ ] `SPEC` als Klassenattribut oder Policy-Property
- [ ] `parse` nur noch `SPEC(raw).map(cls)`
- [ ] Konstruktor laeuft erst nach der Validierung
- [ ] Auspacken per `match` nur an der Systemgrenze
