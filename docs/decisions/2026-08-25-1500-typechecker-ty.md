# Typechecker: `ty` (Astral), scharf ab Tag eins, mit eingefrorener Baseline

Entschieden am 2026-08-25 zu [Issue #97](https://github.com/mbalzert1978/fit_back/issues/97).

## Was entschieden wurde

1. **`ty` (Astral) ist der Typechecker dieses Repos.** Aufgenommen als Dev-Dependency
   (`ty==0.0.74`), konfiguriert in `pyproject.toml` unter `[tool.ty.*]`.
2. **Das Gate läuft scharf, nicht beratend.** `./make.ps1 typecheck` ruft `uv run ty check src`
   und ist Teil von `./make.ps1 ci` — an derselben Stelle und mit demselben Rang wie
   `ruff check`. Ein Typfehler bricht die CI, wie ein Lint-Fehler sie bricht.
3. **Der Ist-Stand ist als Baseline eingefroren, nicht repariert.** Die 37 heutigen Befunde
   stehen als `[[tool.ty.overrides]]`-Blöcke je Dateigruppe in `pyproject.toml`. Jede *neue*
   oder nicht gelistete Datei wird voll geprüft.

## Warum überhaupt

`ruff` ist Linter und Formatter, **kein** Typechecker; es macht keine Typinferenz. Der Beleg aus
dem Issue (`x: int = "keine Zahl"`, vertauschtes Argument, `None`-Zugriff) läuft unter
`ruff check --isolated` mit `All checks passed!` durch. Damit war bis heute jede Typannotation im
Repo Dokumentation, keine Zusage. Dieselbe Datei unter `ty` ergibt vier Befunde
(`invalid-assignment` ×2, `invalid-argument-type`, `unresolved-attribute`).

Konkret blockierte das Loch eine anstehende Entscheidung: die in
`2026-08-21-2309-settings-zugriff-recherche-app-state-versus-dependency.md` dokumentierte
Gegenmaßnahme gegen die `Any`-Typisierung von `app.state` — typisierter Lifespan-State per
`TypedDict` + `Request[State]` — wirkt **rein statisch**. Ohne Typechecker kauft man sie und
niemand löst sie ein.

## Der Ist-Zustand als Zahl

`uv run ty check src` vor jeder Konfiguration: **37 Befunde in 18 Dateien**.

| Regel | Anzahl |
| --- | ---: |
| `invalid-return-type` | 10 |
| `invalid-argument-type` | 8 |
| `type-assertion-failure` | 7 |
| `invalid-assignment` | 6 |
| `unresolved-attribute` | 4 |
| `not-iterable` | 1 |
| `invalid-type-arguments` | 1 |

Nach Ursache gebündelt — so und nicht nach Datei sind die Overrides in `pyproject.toml` gruppiert:

- **`Result` + `Self` (7 Dateien, alle `invalid-return-type`).** `Result[T, E]` ist
  `Ok[T] | Err[E]`. In `classmethod parse(cls) -> Result[Self, E]` engt `ty` `Ok[Self@parse]`
  nicht auf die Klasse ein. Preview-Lücke von `ty`, kein Fehler im Modell.
  **Diese Einschätzung war falsch** — siehe „Abbau der Baseline", Welle 1: es war ein Fehler im
  Modell, und zwar in `result.py` selbst.
- **`assert_never`-Zweige (2 Dateien, `type-assertion-failure`).** `ty` rechnet den Rest-Typ
  nicht auf `Never` herunter, solange der Union-Zweig ein generisches `Err[E]` ist. Damit ist
  `ty` **kein** Ersatz für den werfenden Arm der Exhaustivitäts-Prüfung — siehe die angepasste
  Stelle in `.rules/python/python-control-flow.md`.
  **Nur halb richtig** — siehe „Abbau der Baseline", Welle 2: es lag an der *verschachtelten*
  Form des Musters, nicht am `Err[E]` an sich.
- **Nähte und Protokolle (4 Dateien, `invalid-argument-type`).** `UserStoreTransaction` gegen
  `AsyncConnection`, `DomainEvent` gegen ein konkretes Event, `TaskGroup.create_task` gegen
  `Awaitable` statt `Coroutine`, Pydantics `LaxStr` gegen `str | None`. Hier stecken die
  Kandidaten für echte Funde.
- **Starlette/FastAPI-Grenze (3 Dateien, 5 Regeln).** Handler-Signaturen und
  `Response.body_iterator` (nur auf `StreamingResponse` vorhanden).
- **SQLAlchemy-Stubs (1 Datei, `invalid-assignment`).** `Column[int]` gegen `Column[BigInteger]`:
  die Stubs typisieren über den Python-Wert, die Annotation nennt den SQL-Typ.
- **asyncpg-Verbindung (1 Datei, `unresolved-attribute`)** und **eine `object`-belegte
  Typvariable (1 Datei)**.

## Warum Baseline statt striktem Start oder beratendem Lauf

Verworfen wurde ein **beratendes Target außerhalb von `ci`**: dann prüft niemand neuen Code, weil
niemand den Befehl ausführen muss — das Loch bliebe offen, nur mit installiertem Werkzeug.

Verworfen wurde ebenso ein **strikter Start mit sofortiger Reparatur aller 37 Befunde**: rund die
Hälfte davon sind Preview-Lücken von `ty` (`Self`-Einengung, `assert_never`), nicht Fehler im
Code. Sie zu „reparieren" hieße, das Modell an ein Werkzeug anzupassen, das sich noch bewegt.

Die Baseline hält beides offen: neue Arbeit ist ab sofort geprüft, die Altlast steht namentlich in
`pyproject.toml` und schrumpft, wenn eine Gruppe entweder behoben oder von einem `ty`-Release
eingeholt wird. Eine **neue** Zeile dort gehört begründet.

Belegt, dass das Gate trotz Baseline greift: die Beispieldatei aus dem Issue, in `src/` gelegt,
ergibt weiterhin ihre vier Befunde.

## Abbau der Baseline

Die Baseline wird Welle für Welle abgebaut, indem die Dateien tatsächlich typkorrekt werden. Jede
Welle ist ein eigener Commit und zieht diesen Abschnitt und die Zählung in `pyproject.toml` nach.

### Welle 1 — `Result`-Kovarianz und `Self` (2026-08-26): 37 → 28 Befunde, 18 → 12 Dateien

Der erste Override-Block ist **ersatzlos entfallen** (7 Dateien, `invalid-return-type`). Er war als
Preview-Lücke von `ty` eingetragen; das war eine Fehldiagnose. `Ok`/`Err` waren in ihrem
Typparameter **invariant**, aus zwei Gründen gleichzeitig — beide mussten weg, einer allein wirkte
nicht:

- Die Felder `value`/`error` waren gewöhnliche Dataclass-Felder. `frozen=True` zählt für die
  Varianzberechnung nicht; erst `Final[…]` markiert sie nachweislich als nur lesbar.
- `Err.bind`, `Err.bind_async` und `Ok.or_else` führten den Klassen-Typparameter im Rückgabetyp
  ihrer Fortsetzung, also in kontravarianter Position. Jetzt tragen sie dort einen freien
  Typparameter — diese drei Methoden rufen die Fortsetzung ohnehin nie auf.

Damit passt `Err[EmailAlreadyRegistered]` wieder in eine Kette, die `Err[RegisterUserError]`
verspricht. `pipeline.py` wurde still, ohne selbst angefasst zu werden. Die `parse`-Methoden der
sechs Value Objects geben nun `Result[Self, E]` statt `Result[<Konkret>, E]` zurück — die für einen
`classmethod parse` ohnehin richtigere Signatur.

Verhalten unverändert: `Final[X]` ist für `dataclasses` ein gewöhnliches Feld; `fields`, `__slots__`,
`__eq__`, `match`/`case` und `FrozenInstanceError` bleiben, wie sie waren.

### Welle 2 — Exhaustivität und die Event-Naht (2026-08-26): 28 → 21 Befunde, 12 → 9 Dateien

Zwei weitere Blocks entfallen; auch hier war die eingetragene Begründung in beiden Fällen die
falsche.

**`assert_never` (2 Dateien, ganzer Block entfallen).** Nicht `Err[E]` an sich war das Hindernis,
sondern das *verschachtelte* Muster: aus `case Err(error=EmailIsEmpty())` trägt `ty` die Einengung
nicht in das Typargument von `Err` hinein, der Restfall bleibt `Err[EmailError]`. Das Muster ist
jetzt zweistufig — erst der Ausgang, dann der Fehlerwert selbst:

```python
case Err(error=error):
    match error:
        case EmailIsEmpty():
            ...
        case _:
            assert_never(error)
```

Über einer flachen Union von Fehlerklassen rechnet `ty` die Vollzähligkeit aus. Die
Exhaustivitäts-Prüfung ist damit an diesen Stellen **statisch belegt statt bloß behauptet** — das
ist der eigentliche Gewinn, nicht die gestrichene Baseline-Zeile. Preis: eine Einrückungsebene und
ein zweites `assert_never` je Funktion. Bei der E-Mail-Regel mit fünfzehn Armen zahlt sich das
aus, weil das wiederholte `Err(error=…)` entfällt; bei den kurzen Regeln ist es ein Nullsummen-
Tausch. Die Fallmenge ist unverändert (29 Fehlerklassen vorher wie nachher), ebenso jeder
`FieldError`.

**`DomainEvent` (1 Zeile aus dem Nähte-Block).** `DomainEvent` verlangte `occurred_at` als
schreibbares Attribut. Ein `@dataclass(frozen=True)` wie `UserRegistered` gibt diese Zusage nicht
ab — und soll sie nicht abgeben: ein Ereignis *ist* geschehen, sein Zeitpunkt steht fest. Im
Protocol steht jetzt eine nur lesende `@property`; ein gewöhnliches Feld erfüllt sie, umgekehrt
gilt das nicht. `user_registered.py` und `handler.py` blieben unverändert — der Vertrag war zu
scharf gefordert, nicht das Ereignis zu schwach. Gemessen mit fünf Protokoll-Varianten gegen eine
frozen Dataclass; `EVENT_TYPE` und `to_payload` wichen nicht ab. Nebenwirkung: in `tests/`
verschwinden acht weitere Befunde (`EventRegistry.register` gegen die Obergrenze `DomainEvent`) —
der Beleg, dass die Korrektur an der Naht sitzt und nicht am Einzelfall.

### Welle 3 — die SQLAlchemy-Naht (2026-08-26): 21 → 10 Befunde, 9 → 5 Dateien

Drei Blocks entfallen ganz, einer verliert eine Zeile. Diese Welle enthält die **echten Funde**;
hier war nichts eine Werkzeug-Macke.

**Spalten-Annotationen (`db_schemas.py`, ganzer Block).** `Column` ist in den Stubs über den
**Python**-Wert generisch (`BigInteger` erbt von `TypeEngine[int]`), nicht über den SQL-Typ. Die
Annotationen nannten den SQL-Typ und behaupteten damit schlicht Falsches. Bemerkenswert ist die
Zeile, die `ty` **nicht** beanstandet hat: `Column[Uuid]` war genauso falsch, aber `Uuid` ist über
einen constrained TypeVar generisch, den `ty` aus der nackten Klassenreferenz nicht auflösen kann —
es ergibt `Column[Unknown]`, und `Unknown` ist zu allem zuweisbar. Ein Schweigen des Prüfers ist
also kein Freispruch. Beide Spalten sind mit korrigiert, damit in einer Datei nicht zwei Prinzipien
stehen. Die Tabellendefinition ist unverändert: die `Column(...)`-Argumente sind zeichengleich, das
gegen den Postgres-Dialekt kompilierte `CREATE TABLE` ebenso.

**`UserStoreTransaction` (`user_store.py` + `dependencies.py`).** Hier lagen **zwei** unabhängige
Ursachen übereinander, und die vermutete Folgekette gab es nicht — gemessen, indem zuerst nur die
eine behoben wurde:

1. Der Rückgabetyp `Result[object]` verletzte die Obergrenze `tuple[Any, ...]` von SQLAlchemys
   `Result`. Behoben allein: 21 → 20, die beiden `dependencies.py`-Befunde blieben stehen.
2. `parameters: object` war **kontravariant zu weit**: das Protocol sagte zu, der Aufrufer dürfe
   alles übergeben, während `AsyncConnection.execute` nur `Mapping[str, Any] | Sequence[…] | None`
   annimmt. Ein Implementierer, der weniger annimmt als das Protocol verspricht, erfüllt es nicht.
   `ty` meldete diese Unverträglichkeit an keiner Stelle direkt — sichtbar war sie nur über die
   beiden Aufrufstellen.

`dependencies.py` selbst blieb unverändert; seine zwei Befunde waren reine Folgefehler.

**Outbox-Worker (`worker.py`, ganzer Block).** Der eingetragene Grund („der Worker hält die
Verbindung über seinen Lebenszyklus, ty sieht das nicht") war sachlich falsch. `driver_connection`
ist `Any | None`, und der `None`-Zweig ist **real erreichbar**: steht hinter der Engine keine
DBAPI-Verbindung, lief das bisher in ein `AttributeError` aus der Tiefe — der Worker startete und
hörte einfach nicht zu. Jetzt eine Guard-Klausel, die laut meldet und **degradiert weiterläuft**:
das Polling in `_pump` ist laut Modul-Docstring ohnehin das Sicherheitsnetz für verlorene
Benachrichtigungen, der Schaden ist also Latenz bis `idle_wait_seconds`, nicht Datenverlust. Ein
`raise` wäre hier zudem nicht einmal laut — `run_outbox_worker` startet den Worker per
`asyncio.create_task` und wartet ihn erst beim Shutdown ab; die Exception stürbe still in der Task.

Zwei Nebenfunde, die eigene Tickets verdienen und in dieser Welle bewusst **nicht** angefasst
wurden: `db_schemas.py` steht noch in der 1.x-Form (`declarative_base()` + `Column()`) statt
`Mapped`/`mapped_column` → **Issue #101**; und `IdempotencyKey` hat außerhalb der eigenen Datei
**keinen Verwender** (`alembic/env.py` setzt `target_metadata = None`, die Middleware spricht die
Tabelle über rohe `text(...)`-Statements an), kann also unbemerkt gegen die Migrationen driften —
dafür bewusst **kein** Ticket, das erledigt sich mit den nächsten Endpunkten.

Zum ersten Nebenfund gehört eine Korrektur: hier stand zunächst, die nicht-`Mapped`-Annotation gehe
nur durch, weil Python 3.14 Annotationen verzögert auswertet. **Das war falsch** — nachgemessen mit
SQLAlchemy 2.0.51 auf Python 3.14.5 wird die Form auch mit zur Definitionszeit materialisierten
`__annotations__` akzeptiert, ohne `__allow_unmapped__`. Wir stehen dort nicht auf einer
Zufälligkeit. Der belastbare Grund für #101 ist ein anderer: `nullable=True` lässt sich in dieser
Form nicht ausdrücken — drei nullbare Spalten tragen nicht-optionale Annotationen, also genau die
uneingelöste Zusage, gegen die dieses Ticket angetreten ist.

### Welle 4 — Konfiguration und Nebenläufigkeit (2026-08-26): 10 → 7 Befunde, 5 → 3 Dateien

Der Block `invalid-argument-type` über `settings.py` + `validation.py` entfällt ganz. Beide Befunde
waren echt; die eingetragene Begründung nannte diesmal die Symptome richtig, aber die Lösung lag in
beiden Fällen nicht dort, wo man sie zuerst sucht.

**`settings.py`.** `os.getenv("DB_PASSWORD")` liefert `str | None` an ein Pflichtfeld ohne
Standardwert. Die beiden naheliegenden Abkürzungen sind je eine Verhaltensänderung:
`os.getenv(name, "")` ließe ein leeres Passwort durch (`db_password` hat kein `min_length`), und
`os.environ[name]` würfe `KeyError` **am bestehenden `except` vorbei** — der Startfehler käme dann
nackt statt als `RuntimeError` mit der geheimnisfreien Meldung. Stattdessen ein Helfer, der bei
`None` ein `ValueError` wirft; das fängt das vorhandene `except (ValidationError, ValueError)` und
mündet in genau dieselbe Meldung. Der einzige Unterschied liegt unterhalb der Außengrenze
(`__cause__` ist bei fehlender Variable jetzt `ValueError` statt `ValidationError`); daran hängt im
Repo nichts.

**`validation.py`.** `TaskGroup.create_task` verlangt eine `Coroutine`, `AsyncRule[T]` verspricht
nur ein `Awaitable`. Der Befund ist **auch zur Laufzeit echt**: eine Regel, die ein Objekt mit
`__await__` oder ein `Future` liefert, wäre in `create_task` an einem `TypeError` gescheitert. Der
naheliegende Weg — `AsyncRule` auf `Coroutine[…]` schärfen — scheidet zweimal aus: er bräuchte die
beiden konventionellen `Any`-Parameter, und er verengte die dokumentierte Zusage eines
**öffentlichen** Typs, sodass eine wartbare Regel mit `__await__` kein `AsyncRule` mehr wäre.
Stattdessen wartet ein privater Wrapper (`async def _as_coroutine`) auf das `Awaitable`; ein
`async def`-Aufruf *ist* per Konstruktion eine Coroutine. Nebenläufigkeit und die zugesagte
Ergebnisreihenfolge (Regelreihenfolge, nicht Scheduler-Reihenfolge) bleiben unberührt.

Zwei Nachbesserungen an der Zuarbeit, die zeigen, dass Grün beim Typprüfer nicht das Ende der
Prüfung ist: der Helfer in `settings.py` war zunächst als zweiarmiger `match` formuliert und brach
damit `tests/test_match_exhaustiveness.py` (der letzte Zweig endet nicht laut) — eine Guard-Klausel
tut dasselbe und hält die Regel ein; und sein Bezeichner war der einzige deutschsprachige in ganz
`src/`. Bezeichner sind laut `CLAUDE.md` von der Deutschpflicht ausgenommen, und das Repo führt sie
durchweg englisch.

## Rückfallebene

`ty` ist Preview (`0.0.74`). Erweist es sich als untragbar, sind `mypy` oder `pyright` die
Rückfallebene — beide lesen dieselben Annotationen; neu zu schreiben wäre nur die Konfiguration.
Dieser Hinweis steht auch als Kommentar über dem `[tool.ty.*]`-Block in `pyproject.toml`.

## Was sich dadurch ändert

- `.rules/python/README.md`, `python-types.md`, `python-async.md`, `python-control-flow.md` und
  `python-error-handling.md` behaupteten „kein mypy/pyright" bzw. „dieser Stack läuft ohne
  Typchecker". Das ist ab jetzt falsch und wurde nachgezogen.
- **Jetzt entscheidbar**, was Issue #97 als Folge nennt: ob `app.state` durch einen typisierten
  Lifespan-State ersetzt wird oder ob es beim `request_settings` im Composition Root
  (`src/api/composition.py`) bleibt.
