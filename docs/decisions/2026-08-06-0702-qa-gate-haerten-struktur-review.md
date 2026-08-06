# QA-Gate gehärtet: erschöpfende Regel-Matrix + Tiefen-Struktur-Review + Struktur-Vorabprüfung

## Kontext

PR #9 (Ticket 0008, i18n) und PR #10 (Ticket 0010, Postgres-Outbox) haben beide das
interne QA-Gate (`review-against-rules`, `qa-check`, `solid-principles-check`) mit
`Verdict: APPROVE` durchlaufen. Der Nutzer hat auf GitHub selbst Inline-Review-
Kommentare auf beiden PRs hinterlassen, die reale, substanzielle Architektur- und
Stilverstöße benennen:

- `shared_kernel` (soll dependency-frei sein) hat in beiden PRs externe Dependencies
  bekommen; in PR #10 (`outbox/publisher.py:8`) definieren diese externen Dependencies
  sogar interne Domain-Models mit — Abhängigkeitsrichtung invertiert.
- Durchgängig in PR #9: kein Pattern-Matching (`.rules/python/python-control-flow.md`),
  imperativ statt deklarativ (`python-factories.md`, `python-feature-slices.md`), rohe
  Exceptions statt `Result[T, E]` (`python-error-handling.md`), keine Lookup-Table via
  `dict.get`.
- Tests liegen unter `tests/shared_kernel/...` statt in der vorgesehenen Struktur, teils
  direkt in der Domäne; `main.py` liegt im Repo-Root statt unter `src/`.

## Root Cause

`review-against-rules` delegiert die Prüfung an den `senior-code-reviewer`-Subagenten
mit der Anweisung, „jede Datei unter den konfigurierten Regel-Verzeichnissen zu lesen"
— ohne einen erzwungenen, sichtbaren Prüfweg. Der Subagent konnte dadurch pauschal
`APPROVE` urteilen, ohne belegen zu müssen, welche der zwölf `.rules/python/*`-Dateien
er tatsächlich gegen welche geänderte Datei geprüft hat. Ergebnis: ein plausibel
klingendes Urteil ohne nachprüfbare Grundlage — genau die Klasse Fehler, die
`docs/reflections/exp_verify-subagent-progress-claims.md` bereits für
Fortschrittsmeldungen dokumentiert, hier aber auf Gate-*Urteile* statt auf
Fortschritts-*Meldungen* angewendet.

## Entscheidung

Drei Maßnahmen, alle angewendet:

1. **Erschöpfende Datei-×-Regel-Matrix** (`assets/agent-brief.md` von
   `review-against-rules` geschärft): der Subagent muss vor dem Verdict für jede
   geänderte Datei einzeln gegen jede Regel-Datei Pass/Fail vermerken, mit Begründung
   bei Fail. Eine Regel-Datei, die in der Matrix nicht auftaucht, gilt als ungeprüft,
   nicht als eingehalten.
2. **Tiefen-Struktur-Review als eigenes, nicht optionales Gate**
   (`/thermo-nuclear-code-quality-review` auf den vollständigen Branch-Diff), zusätzlich
   zum bestehenden QA-Gate — deckt Abstraktions-/Deklarativitäts-Verstöße ab, die eine
   reine Regel-Matrix-Prüfung übersehen könnte.
3. **Struktur-Vorabprüfung** vor jedem inhaltlichen Review: rein mechanischer
   Pfad-Check (Testdateien am richtigen Ort, `main.py` unter `src/`) — fängt die
   billigsten, objektivsten Verstöße ab, ohne eine ganze QA-Gate-Runde zu verbrauchen.

Alle drei Änderungen sind in `.claude/agents/fit-back-teamlead.md` (Pipeline-Schritte
4-8) und `.claude/skills/review-against-rules/assets/agent-brief.md` verankert.

## Verifikation (geplant)

Beide gehärteten Gates werden testweise gegen die bestehenden Worktrees/Branches
`0008-m0-i18n-de-de-en-us-resource-files-accept-language-auswertung` und `0010`
laufen gelassen — mit dem Ziel, zu bestätigen, dass sie dieselben vom Nutzer
gefundenen Verstöße tatsächlich selbst aufdecken. Ergebnis wird hier nicht
nachgetragen (siehe Cutoff dieser Session) — bei Bedarf per `git log`/PR-Review-Historie
nachvollziehbar.
