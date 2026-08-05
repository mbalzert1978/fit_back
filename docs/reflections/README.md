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

- [exp_pipeline-artefakte-gitignore.md](exp_pipeline-artefakte-gitignore.md) — Pipeline-Arbeitsdateien (Task.md) von Anfang an gitignored halten
- [exp_powershell-set-content-bom.md](exp_powershell-set-content-bom.md) — PowerShell `Set-Content -Encoding utf8` schreibt eine BOM, bricht TOML-Parser
- [exp_pytest-exit-5-lastexitcode-reset.md](exp_pytest-exit-5-lastexitcode-reset.md) — pytest exit 5 tolerieren UND `$global:LASTEXITCODE` zuruecksetzen
- [exp_security-gate-triage-teamlead.md](exp_security-gate-triage-teamlead.md) — generische Security-Findings ohne Spezifikations-Basis selbst triagieren
- [exp_uv-sync-all-extras.md](exp_uv-sync-all-extras.md) — `uv sync` installiert Extras nicht automatisch, `--all-extras` noetig
- [exp_versionswahl-aktuell-statt-gewohnheit.md](exp_versionswahl-aktuell-statt-gewohnheit.md) — aktuelle stabile Version statt Trainingsdaten-Gewohnheit waehlen
- [exp_workflow-agent-cd-explizit.md](exp_workflow-agent-cd-explizit.md) — Workflow-Pipeline-Prompts brauchen explizites `cd` in den Worktree
- [exp_workflow-tool-args-bug.md](exp_workflow-tool-args-bug.md) — Workflow-Tool `args` kann `undefined` sein, Eingaben hardcoden
