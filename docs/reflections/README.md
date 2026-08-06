# Reflections

Destillierte, wiederverwendbare Lektionen aus vergangenen Sitzungen — Regel +
Begruendung + Anwendungshinweis, kompakter als ein volles Decision-Doc unter
[`docs/decisions/`](../decisions/) und darauf ausgelegt, in einer kuenftigen
Sitzung schnell erfasst zu werden. Dies ist die repo-lokale Entsprechung des
`/reflect`-Skills: **kein** Eintrag landet in Claude Codes sitzungsuebergreifendem
Memory-System, siehe „Entscheidungen und Memory-Policy" in
[`CLAUDE.md`](../../CLAUDE.md) — jede Reflection ist eine normale, versionierte
Datei in diesem Repo.

Format: eine Datei je Lektion (`exp_<kebab-case-name>.md`), Frontmatter mit
`name`/`type`/`frequency`/`last_triggered`/`decay_eligible`, Body mit Regel,
`**Why:**` und `**How to apply:**`. Verweist bei Ueberschneidung auf das
zugehoerige Decision-Doc statt es zu duplizieren.

## Experiences

- [exp_agent-credential-scanning-incident.md](exp_agent-credential-scanning-incident.md) — Subagent darf bei fehlendem `gh` nie selbst nach Credentials suchen, nur stoppen und melden
- [exp_alembic-ini-path-separator-windows.md](exp_alembic-ini-path-separator-windows.md) — `path_separator = os` bricht unter Windows still, wenn `version_locations` mit `":"` authored ist
- [exp_alembic-multi-schema-pitfalls.md](exp_alembic-multi-schema-pitfalls.md) — Revision-IDs global eindeutig halten, `alembic upgrade heads` (Plural) verwenden
- [exp_brief-traegt-die-form-nicht-die-loesung.md](exp_brief-traegt-die-form-nicht-die-loesung.md) — Agenten-Brief beschreibt WAS gelten muss, nie WIE zu loesen ist
- [exp_first-live-execution-surfaces-latent-bugs.md](exp_first-live-execution-surfaces-latent-bugs.md) — erster echter Lauf einer bislang nur "auf dem Papier" existierenden Infrastruktur deckt Bug-Kaskaden auf
- [exp_gh-cli-full-path-required.md](exp_gh-cli-full-path-required.md) — `gh` im Bash-Tool nie ueber PATH aufrufbar, immer vollen Windows-Pfad nutzen
- [exp_gruenes-gate-ohne-scope-angabe.md](exp_gruenes-gate-ohne-scope-angabe.md) — jeder Checker muss seinen tatsaechlichen Pruefumfang mitausgeben, sonst ist „nichts gefunden" nicht von „nichts geprueft" zu unterscheiden
- [exp_maschinelle-absicherung-statt-review-regel.md](exp_maschinelle-absicherung-statt-review-regel.md) — mechanisch entscheidbare Architektur-Regeln gehoeren in einen Linter-Contract, nicht in ein LLM-Review
- [exp_parallele-agenten-brauchen-eigene-worktrees.md](exp_parallele-agenten-brauchen-eigene-worktrees.md) — parallele Agenten im selben Working Tree halten fremde Aenderungen fuer eigene Fehler und raeumen destruktiv auf
- [exp_pipeline-artefakte-gitignore.md](exp_pipeline-artefakte-gitignore.md) — Pipeline-Arbeitsdateien (Task.md) von Anfang an gitignored halten
- [exp_powershell-set-content-bom.md](exp_powershell-set-content-bom.md) — PowerShell `Set-Content -Encoding utf8` schreibt eine BOM, bricht TOML-Parser
- [exp_push-main-before-worktree-fanout.md](exp_push-main-before-worktree-fanout.md) — `main` vor dem Erstellen neuer Worktrees pushen, sonst Scope-Creep in jedem PR-Diff
- [exp_pytest-exit-5-lastexitcode-reset.md](exp_pytest-exit-5-lastexitcode-reset.md) — pytest exit 5 tolerieren UND `$global:LASTEXITCODE` zuruecksetzen
- [exp_referenzimplementierung-schlaegt-prosa.md](exp_referenzimplementierung-schlaegt-prosa.md) — ohne gebautes Referenz-Feature erfindet jeder Agent die Zielform neu
- [exp_regel-lesen-bevor-referenzieren.md](exp_regel-lesen-bevor-referenzieren.md) — eine Regel-Datei, auf die ich verweise, muss ich selbst gelesen haben
- [exp_security-gate-triage-teamlead.md](exp_security-gate-triage-teamlead.md) — generische Security-Findings ohne Spezifikations-Basis selbst triagieren
- [exp_spec-prueft-ergebnis-nicht-implementierung.md](exp_spec-prueft-ergebnis-nicht-implementierung.md) — viele Eingabefaelle rechtfertigen keine tiefere Testebene; fremde Bibliotheken werden nie mitgetestet
- [exp_subprocess-python-literal-vs-sys-executable.md](exp_subprocess-python-literal-vs-sys-executable.md) — `subprocess.run(["python", ...])` loest ueber PATH auf, nicht zum aktiven Venv - `sys.executable` verwenden
- [exp_sqlalchemy-list-bind-needs-any.md](exp_sqlalchemy-list-bind-needs-any.md) — Python-list als SQL-Bind-Param braucht `= ANY(:param)`, nicht `IN (:param)`
- [exp_uv-sync-all-extras.md](exp_uv-sync-all-extras.md) — `uv sync` installiert Extras nicht automatisch, `--all-extras` noetig
- [exp_verify-subagent-progress-claims.md](exp_verify-subagent-progress-claims.md) — Fortschrittsmeldungen von Orchestrator-Agenten per git/gh selbst verifizieren, nie ungeprueft weiterreichen
- [exp_versionswahl-aktuell-statt-gewohnheit.md](exp_versionswahl-aktuell-statt-gewohnheit.md) — aktuelle stabile Version statt Trainingsdaten-Gewohnheit waehlen
- [exp_workflow-agent-cd-explizit.md](exp_workflow-agent-cd-explizit.md) — Workflow-Pipeline-Prompts brauchen explizites `cd` in den Worktree
- [exp_workflow-tool-args-bug.md](exp_workflow-tool-args-bug.md) — Workflow-Tool `args` kann `undefined` sein, Eingaben hardcoden
- [exp_zweifelsfaelle-bericht-deckt-regel-luecken-auf.md](exp_zweifelsfaelle-bericht-deckt-regel-luecken-auf.md) — verpflichtender Zweifelsfall-Bericht im Agenten-Brief ist der billigste Test der eigenen Regel
