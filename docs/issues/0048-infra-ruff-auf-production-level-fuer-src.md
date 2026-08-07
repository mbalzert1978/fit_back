---
id: "0048"
title: "Infra (0008.5): ruff auf Production-Level fuer src/ (select = ALL), Tests ausgenommen"
status: closed
milestone: M0
type: AFK
---

# Infra (laeuft als 0008.5): ruff auf Production-Level fuer `src/` (`select = ALL`), Tests ausgenommen

## What to build

`src/` ist Produktionscode und wird ab sofort entsprechend geprueft: ruff laeuft mit
`select = ["ALL"]`, Ausnahmen nur mit fachlicher Begruendung. Testcode wird sauber gehalten, aber
nicht erzwungen — `tests/**` und `src/contexts/*/specs/**` sind vollstaendig ausgenommen.

## Einplanung: unmittelbar nach 0008, vor jedem weiteren Feature-Ticket

Dieses Ticket laeuft als naechstes, sobald 0008 gemergt ist — nicht ans Ende der Liste, obwohl
seine Nummer das nahelegt. Die Nummer ist hier reine Vergabereihenfolge und **keine**
Planungsaussage; verbindlich ist dieser Abschnitt.

Der Grund ist einfach: jeder Slice, der **nach** diesem Ticket entsteht, wird unter dem scharfen
Gate gebaut und kostet nichts extra. Jeder Slice, der **davor** entsteht, bringt seinen Anteil an
Aufraeumarbeit mit — und die 120 Befunde von heute sind genau das, was sich angesammelt hat,
solange das Gate aus war. Je spaeter das Ticket laeuft, desto groesser die Zahl, die es abarbeiten
muss, und desto mehr Feature-PRs tragen Befunde, die niemand gemeldet hat.

Praktisch heisst das: nach dem Merge von 0008 wird **kein** weiteres Feature-Ticket begonnen,
bevor dieses hier durch ist.

## Warum eigenes Ticket

Bis heute war ausser ruffs Default nur `ANN` aktiv. Damit war fast die gesamte Idiomatik-Pruefung
abgeschaltet, und dieselben Befunde kamen wiederholt aus einem externen Werkzeug (Sourcery) zurueck,
statt vom eigenen Gate — zuletzt `try/except/pass` statt `contextlib.suppress`, verschachtelte `if`,
`x if x else y` statt `x or y`. Mechanisch entscheidbare Regeln gehoeren in den Linter, nicht in ein
Review oder eine Erinnerung
([`exp_maschinelle-absicherung-statt-review-regel.md`](../reflections/exp_maschinelle-absicherung-statt-review-regel.md)).

Gemessen am 2026-08-07: **120 Befunde**, verteilt ueber `src/` und `alembic/`, quer durch rund 25
Dateien. Deshalb ein eigenes Ticket — in einem Feature-PR wuerde der Diff die eigentliche Aenderung
ersaeufen.

## Die Konfiguration

Wortlaut, bereits kuratiert und gemessen; sie ersetzt den bisherigen `[tool.ruff.lint]`-Block in
`pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["ALL"]

ignore = [
    "CPY001",  # Copyright-Kopf je Datei - dieses Repo hat die Konvention nicht
    "COM812",  # Trailing-Comma-Regel kollidiert mit dem ruff-Formatter (dessen eigene Warnung)
    "ISC001",  # implizite String-Verkettung - dieselbe Kollision mit dem Formatter
    "D203",    # unvereinbar mit D211; ruff waehlt ohnehin D211
    "D213",    # unvereinbar mit D212; ruff waehlt ohnehin D212
    "D401",    # "imperative mood" ist eine Heuristik auf englischen Verben; die
               # Docstrings dieses Repos sind deutsch (CLAUDE.md), die Regel misst dort nichts
    "TC001",   # Imports unter `if TYPE_CHECKING` verstecken. Dieser Stack laeuft bewusst ohne
    "TC002",   # mypy/pyright (.rules/python/README.md) - die Trennung braechte keinen Nutzen,
    "TC003",   # und zur Laufzeit aufloesbare Annotationen sind uns lieber als gesparte Imports
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ALL"]
"src/contexts/*/specs/**" = ["ALL"]
```

**Ausdruecklich nicht ausgenommen:** `application/<use_case>/test_api/` und `fakes/`. Beide sind
laut [`python-feature-slices.md`](../../.rules/python/python-feature-slices.md) ausgelieferter Teil
des Slice und damit Produktionscode, auch wenn „test" im Namen steht.

## Offene Urteile beim Aufraeumen

Vier Gruppen brauchen eine Entscheidung statt einer mechanischen Korrektur. Jede wird entweder
behoben **oder** mit `# noqa: CODE -- Begruendung` an der betroffenen Zeile stehen gelassen
(Format nach [`python-modern-syntax.md`](../../.rules/python/python-modern-syntax.md)), nie global
ignoriert:

- **`INP001` (12x)** — die `alembic/*/versions/`-Verzeichnisse haben kein `__init__.py`. Sie sind
  auch keine importierbaren Pakete: Alembic laedt die Revisionen ueber seinen eigenen Mechanismus.
  Vermutlich eine gerechtfertigte Ausnahme fuer diesen Pfad — pruefen und dann **mit Begruendung**
  in die Konfiguration, nicht per Datei-noqa.
- **`S608` (4x)** — „hardcoded SQL". Betrifft die `text()`-Statements mit gebundenen Parametern,
  die dieses Repo bewusst statt eines ORM-Query-Builders verwendet. Pruefen, dass wirklich
  ueberall gebunden wird, dann verorteter `# noqa` mit Begruendung.
- **`TRY003`/`EM101`/`EM102` (26x)** — Ausnahmetexte direkt im `raise`. Die Regel will sie als
  Variable davor. Einheitlich umsetzen, nicht mischen.
- **`PLR0913`/`PLR0917`/`C901`/`PLR0912`/`PLR0911` (12x)** — zu viele Argumente, zu hohe
  Komplexitaet. Hier ist die Frage, ob die Stelle wirklich zu gross ist oder die Grenze zu eng.
  Beides ist zulaessig, aber es braucht je Fall ein Urteil.

`D104` (23x, Docstring in `__init__.py`) und `D103` (22x) sind reine Fleissarbeit ohne Urteil.

## Acceptance criteria

- [ ] Der `[tool.ruff.lint]`-Block aus diesem Ticket steht in `pyproject.toml`
- [ ] `uv run ruff check .` meldet `All checks passed!`
- [ ] `uv run ruff format --check .` bleibt gruen
- [ ] `uv run pytest` bleibt bei der Zahl bestandener Tests von vor dem Ticket — **kein** Test
      wird geloescht oder uebersprungen, um Befunde loszuwerden
- [ ] Jede verbliebene Unterdrueckung ist entweder ein `ignore`-Eintrag mit fachlicher Begruendung
      im Kommentar oder ein verorteter `# noqa: CODE -- Begruendung`; kein nacktes `# noqa`, kein
      dateiweites `# ruff: noqa`
- [ ] Die vier Gruppen unter „Offene Urteile" sind je einzeln entschieden und die Entscheidung ist
      im PR nachvollziehbar begruendet

## Blocked by

- Blocked by [0008](0008-m0-i18n-de-de-en-us-resource-files-accept-language-auswertung.md) — nur
  zeitlich: 0008 fasst dieselben Dateien an, parallel gaebe es nur Konflikte

## Abschluss (2026-08-07)

Umgesetzt und gemergt als PR #14 („Infra (0048): ruff auf Production-Level fuer src/
(select = ALL)", Squash-Merge, `a26126c` auf `main`). Der Inhalt wurde nach dem Merge per
`git diff origin/main <branch-head>` als identisch verifiziert; Worktree und lokaler Branch
sind abgebaut.

Die Acceptance criteria sind erfuellt: der `[tool.ruff.lint]`-Block steht im Wortlaut des
Tickets in `pyproject.toml`, `ruff check` meldet `All checks passed!`, `ruff format --check`
bleibt gruen, und `pytest` liefert unveraendert **280 passed** — keine Testdatei unter
`tests/` oder `src/contexts/*/specs/` wurde angefasst. Jede Unterdrueckung ist entweder ein
begruendeter `ignore`-Eintrag oder ein verorteter `# noqa: CODE -- Begruendung`; kein nacktes
`# noqa`, kein dateiweites `# ruff: noqa`.

Die vier offenen Urteile wurden je einzeln entschieden:

- **`INP001`** — `per-file-ignores` fuer `alembic/*/versions/**` und `alembic/env.py`, weil
  Alembic seine Revisionen ueber einen eigenen Mechanismus laedt. Konfiguration statt
  Datei-`noqa`, weil die Ausnahme dem ganzen Pfad gilt.
- **`S608`** — verorteter `# noqa`. In `src/middleware/idempotency.py` wird ausschliesslich die
  Modulkonstante `IDEMPOTENCY_KEYS_TABLE` (`:79`, Literal) interpoliert; jeder Nutzerwert laeuft
  ueber Named Binds. Im Security-Gate einzeln nachgeprueft.
- **`TRY003`/`EM101`/`EM102`** — keine Befunde mehr. Die im Ticket genannten 26 stammen aus einer
  Messung vor dem Merge von 0008, das die Texte aus den `raise`-Statements in die Resource-Files
  gezogen hat. Mit `ruff check --select TRY003,EM101,EM102 --ignore-noqa` gegengeprueft: 0.
- **`PLR0913`/`PLR0917`/`C901`/`PLR0912`/`PLR0911`** — verortete `# noqa` mit fallweiser
  Begruendung. Eine Umstrukturierung haette Verhalten geaendert, was dieses Ticket ausschliesst.

Ergaenzend entschieden: Docstrings werden einheitlich **deutsch** verfasst, entsprechend der
gelebten Praxis im Repo und der `D401`-Begruendung in der Konfiguration selbst. Die vier
ungenutzten Parameter in `src/contexts/shared_kernel/result.py` heissen `_` und sind zusaetzlich
positional-only (`/`), damit die beiden Arme der Tagged Union `Result[T, E]` austauschbar bleiben.
