# CI-Nacharbeiten nach Ticket-0002-Merge

**Entschieden:** 2026-08-05 11:10

## Was

Nach dem Merge von PR #4 (Ticket 0002, ruff/import-linter/Lint-CI) wurde `main` und alle
drei offenen Welle-2-PRs (#2/Ticket 0003, #3/Ticket 0004, #5/Ticket 0005) rot. Direkt auf
`main` behoben, dann in jeden offenen Branch gemergt:

1. **main.py-Altlasten:** Sobald die ruff-Config existierte, schlugen bestehende Regeln
   (`UP035`, `ANN204`, `ANN001`) retroaktiv gegen `main.py`-Code an, der vor der Config
   geschrieben wurde. Gefixt (Import von `collections.abc.Callable`, fehlende
   Typannotationen an `RateLimitMiddleware.__init__`).
2. **Log-Hygiene-Regression:** Der legitime Security-Fix-Commit auf Ticket 0002 hatte
   `str(e)` zurueck in zwei Log-Meldungen gebracht (`init_db`, `health_check`) — exakt das
   Muster, das fuer Ticket 0001 bereits als Finding gefixt wurde (siehe
   `2026-08-05-0936-...`). Erneut auf bare Messages ohne Exception-Details zurueckgesetzt.
3. **Fehlende Dev-Extras in CI:** `ruff`/`import-linter`/`pytest` stehen unter
   `[project.optional-dependencies].dev`; ein bloßes `uv sync` installiert Extras nicht.
   CI und `make.ps1 install` liefen deshalb faktisch ohne diese Tools. Beide auf
   `uv sync --all-extras` umgestellt.
4. **pytest exit 5 bei 0 Tests:** Tooling-only-Tickets (0002, 0003) liefern noch keine
   Testdateien — `pytest` meldet dafuer exit code 5 ("no tests ran"), was `make.ps1`s
   `test`-Target bislang als Fehler wertete, obwohl Ticket 0009 genau diesen Zustand
   („0 Tests, kein Fehler") explizit als Zielverhalten spezifiziert. Zusaetzlich musste
   nach dem ersten Fix `$global:LASTEXITCODE` explizit zurueckgesetzt werden, da
   PowerShell den Exit-Code des letzten nativen Kommandos sonst weiterhin als
   Skript-Exit-Code durchreicht, selbst wenn kein `throw` mehr ausgeloest wird.

Alle vier Fixes wurden auf `main` committet und in die drei offenen Ticket-Branches
gemergt/gepusht; alle drei PRs (#2, #3, #5) sind danach gruen (verifiziert per
`gh pr checks`).

## Warum

Diese Fixes sind Infrastruktur-/Tooling-Nacharbeiten, keine Produktentscheidungen —
deshalb hier nur knapp dokumentiert statt einzeln je Fund. Sie folgen demselben
Prinzip wie bereits etabliert: retroaktiv auffallende Verstoesse werden direkt behoben,
nicht auf spaetere Tickets verschoben, wenn der Fix trivial und im Scope „macht CI
gruen" liegt.

## Was das ausschliesst

- Keine neuen Tickets noetig — alle Fixes sind in den bereits laufenden Branches
  (main + 0003/0004/0005) enthalten.
- Aendert nichts an der fachlichen Spezifikation der betroffenen Tickets.
