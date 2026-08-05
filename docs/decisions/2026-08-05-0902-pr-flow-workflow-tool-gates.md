# PR-Flow statt Auto-Merge, Workflow-Tool-Orchestrierung, Parallelitäts-Cap, zusätzliche Gates

**Entschieden:** 2026-08-05 09:02

## Was

Ergänzt/präzisiert
[`2026-08-05-0839-implementation-pipeline-and-wave-1.md`](2026-08-05-0839-implementation-pipeline-and-wave-1.md)
und
[`2026-08-05-0851-pipeline-vollautomatisiert-inkl-entwicklerrolle.md`](2026-08-05-0851-pipeline-vollautomatisiert-inkl-entwicklerrolle.md)
um vier vom Stakeholder entschiedene Punkte, die vor dem tatsächlichen Start von Welle 1
abgestimmt wurden.

### 1. Merge-Schritt wird zu PR-Schritt

**Entscheidung:** Statt direkt nach `main` zu mergen, pusht die Pipeline den Ticket-Branch zum
`origin`-Remote (`github.com/mbalzert1978/fit_back`) und öffnet über `gh pr create` einen Pull
Request gegen `main`. **Der Stakeholder reviewt und merged den PR selbst** — das ist keine
Pipeline-Stufe mehr, die ich ausführe.

**Status `gh`:** installiert (`GitHub CLI 2.97.0`, via winget), aber **nicht authentifiziert** —
`gh auth login` ist ein interaktiver Schritt (Browser/Token), den nur der Stakeholder selbst
ausführen kann. Bis dahin endet die Pipeline für ein Ticket nach bestandenem Security-Gate mit
einem gepushten Branch und einem vorbereiteten PR-Text, aber ohne tatsächlich ausgeführtes
`gh pr create`; sobald `gh auth status` grün ist, wird dieser letzte Schritt nachgeholt.

**Ersetzt** aus `2026-08-05-0839`, Pipeline-Punkt 6: „Merge — … wird der Ticket-Branch nach
`main` gemerged" → wird zu „Branch pushen + PR öffnen; Merge macht ausschließlich der
Stakeholder".

### 2. Orchestrierung über das Workflow-Tool

**Entscheidung:** Die Wellen-Pipeline (Entwicklung → QA → Security → PR, inkl. Fix-Verify-Loops)
läuft über das `Workflow`-Tool, nicht über direkte `Agent`-Aufrufe durch mich im laufenden
Gespräch — vom Stakeholder ausdrücklich als „Empfohlen" bestätigt (Opt-in für
Multi-Agent-Orchestrierung).

**Warum:** Workflows laufen im Hintergrund und sind resumable (`resumeFromRunId`) — das adressiert
direkt die Sorge des Stakeholders vor Auto-Compact mitten im Ablauf: die eigentliche Schwerarbeit
(Diffs lesen, Code schreiben, Tests laufen lassen) passiert im Kontext der Workflow-Subagenten,
nicht in meinem Hauptkontext, der dadurch klein bleibt.

**Bekannte Einschränkung, transparent gemacht:** Das Workflow-Tool unterstützt kein
konversationelles „denselben Agenten fortsetzen" wie das direkte `Agent`-Tool
(kein SendMessage-Äquivalent zwischen `agent()`-Aufrufen). Die in `2026-08-05-0839` getroffene
Entscheidung „derselbe Entwickler-Agent behebt Fixes" wird im Workflow dadurch angenähert, dass
jeder Fix-Aufruf als neuer `agent()`-Call denselben Worktree-Pfad erhält **plus** den vollen
Kontext (ursprünglicher Diff, Ticket, QA-/Security-Findings) im Prompt — inhaltlich dieselbe
Absicht (kontextreiche, gezielte Fixes statt blinder Neuschriebe), technisch aber ein neuer
Agent-Aufruf statt einer echten Fortsetzung. Das wird hier bewusst festgehalten, damit es nicht
stillschweigend von der ursprünglichen Entscheidung abweicht.

**Was weiterhin außerhalb des Workflows läuft:** Worktree-Anlage (`/worktree-erstellen`) und
`Task.md`-Erzeugung (`/refine-prompt`) sind deterministisch, günstig und nicht parallelitätskritisch
— die erledige ich weiterhin direkt (Bash/Skill-Aufrufe), bevor ich den Workflow für die
eigentliche Entwicklungs-/QA-/Security-Kette startet. Das hält den Workflow selbst schlank.

### 3. Parallelitäts-Obergrenze: 3 Tickets gleichzeitig

**Entscheidung:** Höchstens **3 Tickets gleichzeitig in Bearbeitung**, unabhängig davon, wie viele
der Abhängigkeitsgraph als gegenseitig unabhängig zuließe — vom Stakeholder mit Verweis auf die
Kapazität der aktuellen Maschine festgelegt.

**Konsequenz für Wellen:** Hat eine Welle mehr als 3 startbereite Tickets (z. B. Welle 2 mit vier
Kandidaten: 0002/0003/0004/0005), wird sie in Batches von ≤3 verarbeitet, nicht komplett auf
einmal gestartet.

### 4. Zusätzliche Kontroll-Gates

**Entscheidung:** Zwei zusätzliche Gates, beide vom Stakeholder bestätigt:

- **Post-Merge-Regressions-Check auf `main`** — implementiert über die neue CI/CD-Pipeline (siehe
  unten): der GitHub-Actions-Workflow läuft nicht nur auf `pull_request`, sondern auch auf jedem
  `push` nach `main`. Ein grüner Ticket-PR schließt damit nicht aus, dass der Merge in Kombination
  mit bereits gemergten Geschwister-Tickets etwas bricht — das fängt dieser zusätzliche Lauf auf
  `main` selbst ab, unabhängig vom einzelnen PR-Check.
- **`architecture-adr-check` für die sechs Cross-Context-Tickets** (0011, 0017, 0018, 0026, 0038,
  0042 — Outbox-/Port-Pattern) als zusätzlicher QA-Schritt neben `review-against-rules`,
  `qa-check`, `solid-principles-check`. Für alle anderen Tickets bleibt die QA-Stufe wie in
  `2026-08-05-0839` beschrieben.

**Zusätzlich beauftragt:** eine echte CI/CD-Pipeline für PRs (nicht nur ein lokal ausgeführtes
Gate) — siehe `.github/workflows/ci.yml`: läuft auf `pull_request` (Ziel `main`) und auf `push`
nach `main`, führt `./make.ps1 ci` aus (lint + format-check + import-lint + test) auf
`ubuntu-latest` mit `pwsh`. Solange Ticket 0002 (ruff-Konfiguration, `.importlinter`-Contract)
noch nicht gemerged ist, werden `lint`/`import-lint` dort absehbar rot laufen (kein Contract, keine
Ruff-Konfiguration) — das ist für Ticket 0001 selbst kein Blocker, da es kein per-Ticket
Merge-Gate durch mich mehr gibt (siehe Punkt 1: der Stakeholder entscheidet über den PR-Merge
selbst und sieht den CI-Status dabei).

## Was das ausschließt / ersetzt

- Ersetzt in `2026-08-05-0839`, Punkt 6: „Merge" wird zu „Branch pushen + PR öffnen"; ich merge
  nie mehr selbst nach `main`.
- Schließt aus, dass ich Fix-Verify-Zyklen als echte Multi-Turn-Konversation mit demselben Agenten
  führe, solange über das Workflow-Tool orchestriert wird — die Absicht (kontextreicher Fix)
  bleibt, der Mechanismus (neuer `agent()`-Call pro Zyklus) ändert sich.
- Schließt aus, mehr als 3 Tickets gleichzeitig in aktiver Bearbeitung zu haben, auch wenn der
  Abhängigkeitsgraph mehr zuließe.
- Führt `architecture-adr-check` nur für die sechs benannten Cross-Context-Tickets ein, nicht als
  generelles Gate für alle Tickets.
