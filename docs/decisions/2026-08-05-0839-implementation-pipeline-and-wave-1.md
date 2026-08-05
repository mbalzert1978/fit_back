# Implementierungspipeline und Auswahl von Welle 1

**Entschieden:** 2026-08-05 08:39

## Was

Diese Entscheidung legt, als Team-Lead-Engineer, fest, wie Tickets unter `docs/issues/` von
„open" bis „nach `main` gemerged" durchlaufen, und wählt die erste Welle an Tickets aus, die
ausgegeben wird.

### Pipeline (je Ticket)

1. **Worktree** — pro Ticket einen Worktree über `/worktree-erstellen` anlegen
   (`.claude/worktrees/<ticket-id>-<slug>`, Branch gleich benannt). Ein Worktree je Ticket, nie
   geteilt. Gemäß dem repo-spezifischen Hinweis des Skills `.rules/` im Anschluss von Hand in den
   Worktree verlinken (Junction) — es ist gitignored und keines der vom Skill gespiegelten Ziele.
2. **Task.md** — `/refine-prompt` auf den Ticket-Body (Titel, „What to build",
   „Acceptance criteria", „Blocked by") anwenden, um einen gehärteten Task-Prompt zu erzeugen,
   und diesen als `Task.md` im Worktree-Root ablegen. `/refine-prompt` schreibt nur um; es
   implementiert nie — die dabei erzeugte `Task.md` ist das, womit der Entwickler-Agent aus
   Schritt 3 tatsächlich gebrieft wird.
3. **Entwickler-Rolle** — ein Entwickler-Agent implementiert das Ticket im Worktree gemäß
   `Task.md`. **Ich starte diesen Agenten nicht.** Der Nutzer startet ihn manuell, sobald
   Worktree und `Task.md` vorliegen. Dieser Schritt endet mit einem Kandidaten-Diff auf dem
   Ticket-Branch.
4. **QA-Rolle** — sobald der Entwickler die Implementierung als fertig meldet, wird der Worktree
   an eine QA-Prüfung delegiert:
   - `review-against-rules` — Diff gegen `.rules/common/` + `.rules/python/` (bereits die
     konfigurierten `rules_dirs`).
   - `qa-check` — führt die Testsuite (`run-tests`) sowie die aktuell aktivierten Checks aus (die
     Checks `coverage_gap`/`test_api_shape` bleiben laut eigenem `_note` deaktiviert, bis eine
     Referenz-Implementierung existiert — siehe offener Punkt unten).
   - `solid-principles-check` — SOLID-Smells auf dem Diff.

   **Fix-Verify-Loop:** jedes BLOCK/FAIL geht zurück an **denselben Entwickler-Agenten**, der
   implementiert hat (im selben Worktree fortgesetzt, kein neuer Agent — siehe „Wer behebt die
   Fixes" unten), der behebt, woraufhin QA erneut läuft. Max. **3** QA-Durchläufe. Besteht das
   Ticket auch nach Durchlauf 3 nicht, **stoppt die Pipeline für dieses Ticket** und wird an mich
   (Team-Lead) eskaliert, statt weiter zu loopen oder trotzdem zu mergen.
5. **Security-Rolle** — erst nach bestandener QA wird derselbe Worktree an eine Security-Prüfung
   delegiert. In diesem Repo existiert kein dedizierter `security-review`-Skill; die passendste
   Wahl ist `review-against-rules`, gezielt auf `.rules/common/security.md` fokussiert (bereits
   Teil der konfigurierten `rules_dirs` — also ein erneuter Lauf mit auf diese eine Datei
   verengter Aufmerksamkeit statt eines neuen Skills). Gleiche **Fix-Verify-Loop**-Semantik wie
   bei QA: derselbe Entwickler-Agent behebt, max. **3** Durchläufe, danach Eskalation an mich bei
   fortbestehenden Findings — kein automatischer Merge nach drei gescheiterten
   Security-Durchläufen.
6. **Merge** — erst nachdem QA **und** Security bestanden sind (jeweils innerhalb ihrer 3er-Kappe),
   wird der Ticket-Branch nach `main` gemerged. Timing siehe „Merge-Granularität" unten.

### Offener Punkt 1 — Merge-Granularität: pro Ticket, nicht pro Welle

**Entscheidung: jedes Ticket wird einzeln nach `main` gemerged, sobald seine eigene QA+Security
bestanden ist** — nicht gebündelt am Ende der Welle.

**Warum:** das gesamte Tracer-Bullet-Design von `to-issues` prüft bereits auf „unabhängig
verifizierbar" (Kriterium 4 von `verify-issue-breakdown`) — jedes Ticket ist so gedacht, dass es
für sich demo- und mergefähig ist. Merges am Wellenende zu bündeln würde (a) genau den
Big-Bang-Integrations-Merge erzeugen, den die Tracer-Bullet-Zerlegung vermeiden sollte, (b) `main`
davon abhalten, ein tatsächlich fertiges und beide Gates bestandenes Ticket zu widerspiegeln, und
(c) dazu führen, dass ein nachhinkendes Ticket in einer Welle den Merge aller sonst unabhängigen
Geschwister-Tickets blockiert. Wellen begrenzen, *wie viel Arbeit parallel in Flight ist* — nicht,
wie Merges gebündelt werden.

### Offener Punkt 2 — Wer behebt die Fixes im Loop: derselbe Entwickler-Agent, keine eigene Fix-Rolle

**Entscheidung: derselbe Entwickler-Agent, der das Ticket implementiert hat, behebt auch die
Fixes**, fortgesetzt im eigenen Worktree — keine eigene „Fixer"-Rolle.

**Warum:** dieser Agent hält bereits den vollständigen Kontext der Implementierung (warum er den
Code so strukturiert hat, welche Design-Abwägungen er innerhalb des Ticket-Scopes getroffen hat)
— ein frischer Fix-Agent müsste diesen Kontext allein aus dem Diff rekonstruieren und liefe
Gefahr, eine bewusste Entscheidung zu widersprechen statt einen tatsächlichen Fehler zu beheben.
Das spiegelt, wie dieses Repo Fixer/Verifier-Paare unter `.claude/skills/` bereits behandelt
(`fixer-*`-Skills wenden die *verorteten* Findings ihres gepaarten `verifier-*` an, keine blinden
Neuschriebe) — dasselbe Prinzip, angewandt auf einen nutzergetriggerten Implementierungs-Loop
statt ein Skill-Paar.

### Eskalation statt stillem Stopp

Beide Loops (QA und Security) eskalieren nach 3 gescheiterten Durchläufen an mich, statt still zu
stoppen oder trotzdem fortzufahren — passend zur Vorgabe „offene Entscheidungen dem Nutzer
vorlegen statt einseitig entscheiden", unter der diese gesamte Implementierung steht.

## Welle 1

**Welle 1 = nur Ticket 0001** —
[`0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test`](../issues/0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test.md).

Jeden „## Blocked by"-Abschnitt der M0-Tickets direkt geprüft (`docs/issues/0001`–`0010`, `0046`):
0001 ist das **einzige** Ticket im gesamten Backlog mit `Blocked by: None - can start immediately`.
Jedes andere M0-Ticket (0002–0005) ist durch 0001 selbst blockiert; 0006/0007/0009/0010 hängen
weiter über 0003/0004 dran; 0046 über 0006. Jedes Ticket ab M1 ist (direkt oder transitiv, über
die im jeweiligen Meilenstein festgelegte Abhängigkeit in
[`00-overview.md`](../milestones/00-overview.md)) durch ganz M0 blockiert. Da keiner der
Nachfolger von 0001 starten kann, bevor 0001 selbst gemerged ist, würde eine Welle, die sie
enthält, die Vorgabe „kein Ticket ohne erfüllte Vorbedingungen" verletzen — Welle 1 kann also
nicht größer als `{0001}` sein, ohne die Startbereitschaft schlicht vorzutäuschen.

Das ist für ein Repo bei null erwartbar und korrekt: Das erste Ticket von M0 selbst ist das
technische Fundament (Repo-Skeleton, docker-compose mit postgres/minio/app, Health-Endpoint,
curl-Smoke-Test), das jedes andere Ticket im Backlog voraussetzt. Direkt danach öffnet sich die
Parallelität.

**Welle-2-Kandidaten** (werden startbereit — `status: open`, nicht `blocked` — sobald 0001
gemerged ist; daraus die nächste Welle planen, sobald Welle 1 abgeschlossen ist): 0002
(ruff + import-linter), 0003 (Alembic-7-Schema-Grundgerüst), 0004 (Shared-Kernel
`Result`/`TimeProvider`), 0005 (RFC-7807-ProblemDetails). Alle vier sind ausschließlich durch 0001
blockiert, überschneiden sich konstruktionsbedingt in keiner Datei (getrennte Belange: Lint-Config,
Migrationen, Shared-Kernel-VO/Result-Typen, Exception-Handling-Middleware) und können in vier
parallelen Worktrees laufen.

## Was das ausschließt / ersetzt

- Schließt aus, Tickets in wellengroßen Batches zu mergen — jedes Ticket wird gemerged, sobald es
  individuell QA+Security besteht, unabhängig vom Status der Wellen-Geschwister.
- Schließt aus, eine eigene „Fixer-Agent"-Rolle für den Implementierungs-Fix-Verify-Loop
  einzuführen — Fixes bleiben beim ursprünglichen Entwickler-Agenten in dessen eigenem Worktree.
- Führt keinen neuen `security-review`-Skill ein; nutzt explizit `review-against-rules`, fokussiert
  auf `.rules/common/security.md`, weiter, bis/falls ein dedizierter Security-Review-Skill zu
  `.claude/skills/` hinzukommt (dann revisitieren, analog zu den bereits offenen
  Referenz-Implementierungs-Folgepunkten von `qa-check`/`review-against-rules` in deren eigenen
  `config.json`-`_note`-Feldern).
