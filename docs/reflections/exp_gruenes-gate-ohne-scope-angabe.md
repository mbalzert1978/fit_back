---
schema_version: 1
name: gruenes-gate-ohne-scope-angabe
description: Ein Gate, das APPROVE meldet ohne zu sagen WIE VIEL es geprueft hat, ist nicht unterscheidbar von einem Gate, das nichts gefunden hat - jeder Checker muss seinen tatsaechlichen Pruefumfang mitausgeben
type: project
frequency: 2
last_triggered: 2026-08-06
decay_eligible: false
---

Jeder Checker gibt neben dem Verdikt aus, **wie viel er tatsaechlich inspiziert hat** („`Scope: 0
use case(s), 0 spec file(s) inspected`"). Ohne diese Zeile ist „nichts gefunden" nicht von „nichts
geprueft" zu unterscheiden — und beide sehen als `Verdict: APPROVE` identisch aus.

**Why:** Beim Bau von `slice-shape-check` fiel auf, dass das Skill im aktuellen Repo-Zustand
zwangslaeufig `APPROVE` liefert, weil es (noch) **null** Use-Case-Pakete gibt — M0 hatte
ausschliesslich Infrastruktur gebaut. Ein blosses `Verdict: APPROVE / Findings: 0` haette in jeder
Pipeline-Ausgabe wie eine bestandene Pruefung ausgesehen und der Slice-Form-Verstoss waere weiter
unbemerkt geblieben. Dasselbe Muster erklaert rueckblickend, warum das QA-Gate ganze M0-PRs
durchwinkte: es urteilte pauschal, ohne seinen Pruefweg sichtbar zu machen (siehe
`docs/decisions/2026-08-06-0702-qa-gate-haerten-struktur-review.md`, dort geloest ueber eine
erzwungene Datei-x-Regel-Matrix).

**How to apply:** Beim Schreiben oder Schaerfen eines Verifiers: eine `Scope:`-Zeile (oder eine
Pruefmatrix) verpflichtend in das Ausgabeformat aufnehmen und im `SKILL.md` explizit vermerken,
dass ein Leser sie mitlesen muss. Beim *Lesen* eines fremden Gate-Ergebnisses: vor dem Vertrauen in
ein `APPROVE` immer fragen, wie viele Einheiten es angefasst hat — fehlt die Angabe, ist das
Ergebnis nicht belastbar. Verwandt:
[exp_verify-subagent-progress-claims.md](exp_verify-subagent-progress-claims.md).
