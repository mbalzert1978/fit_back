# Pipeline vollautomatisiert inkl. Entwickler-Rolle — parallele Wellen über Worktrees

**Entschieden:** 2026-08-05 08:51

## Was

Ergänzt/ersetzt Punkt 3 („Entwickler-Rolle") aus
[`2026-08-05-0839-implementation-pipeline-and-wave-1.md`](2026-08-05-0839-implementation-pipeline-and-wave-1.md).
Auf ausdrücklichen Wunsch des Auftraggebers orchestriere ich ab sofort **die gesamte Pipeline
selbst** — Worktree, Task.md, Entwickler-Rolle, QA, Security, Merge — ohne manuellen Start durch
den Nutzer. Das war zuvor die einzige Stufe, die der Nutzer selbst anstoßen wollte; das entfällt
hiermit.

**Konkret:**
- Ich starte den Entwickler-Agenten pro Ticket selbst (nicht mehr der Nutzer), im Anschluss an das
  Anlegen von Worktree + `Task.md`.
- Wo mehrere Tickets einer Welle gegeneinander unabhängig sind (keine Blocked-by-Kante, keine
  gemeinsam berührten Dateien/Verzeichnisse laut ihrem jeweiligen „What to build"), starte ich
  ihre Entwickler-Agenten **echt parallel**, jeden in seinem eigenen, über `/worktree-erstellen`
  angelegten Worktree unter `.claude/worktrees/<ticket-id>-<slug>`. Wellen sind damit keine
  sequenzielle Abarbeitung mit paralleler Fiktion, sondern tatsächlich gleichzeitig laufende
  Agenten.
- Alle übrigen Punkte der ursprünglichen Entscheidung bleiben unverändert gültig: ein Worktree je
  Ticket, `.rules/`-Junction von Hand, Fix-Verify-Loop mit max. 3 Durchläufen durch denselben
  Entwickler-Agenten, Eskalation an den Nutzer statt stillem Stopp, Merge pro Ticket einzeln
  sobald QA+Security bestanden sind.

## Warum

Der Nutzer hat die vorherige Einschränkung („Ich starte diesen Agenten nicht — der Nutzer startet
ihn manuell") explizit aufgehoben und darum gebeten, dass ich ab jetzt die komplette Pipeline
orchestriere, einschließlich Wellen, die tatsächlich parallel laufen — ausdrücklich über
Worktrees, nicht als bloße Konzept-Parallelität. Das war eine bewusste Entscheidung des
Auftraggebers, keine einseitige technische Wahl von mir.

## Was das ausschließt / ersetzt

- Ersetzt den Satz „Ich starte diesen Agenten nicht. Der Nutzer startet ihn manuell." aus Punkt 3
  von `2026-08-05-0839-implementation-pipeline-and-wave-1.md` — dieser Teil gilt ab sofort nicht
  mehr.
- Schließt weiterhin aus: Wave-Parallelität ohne Worktree-Isolation (jede parallele Ticket-Arbeit
  läuft in ihrem eigenen, über `/worktree-erstellen` angelegten Worktree — nie im selben
  Arbeitsverzeichnis).
- Ändert nichts an QA-/Security-Gates, Fix-Verify-Loop-Obergrenze (3) oder der
  Eskalationsregel — Automatisierung des Entwickler-Starts ist kein Freibrief für automatischen
  Merge ohne bestandene Gates.
