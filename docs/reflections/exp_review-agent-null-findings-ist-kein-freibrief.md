---
schema_version: 1
name: review-agent-null-findings-ist-kein-freibrief
description: Ein Review-Agent, der APPROVE mit 0 Findings meldet, hat nichts belegt - besonders eine lueckenlos gruene Pruefmatrix und selbst geschlossene Zweifelsfaelle sind Warnsignale, keine Bestaetigung
type: feedback
frequency: 2
last_triggered: 2026-08-06
decay_eligible: false
---

Ein `APPROVE` mit `Findings: 0` von einem Review-Agenten ist ein **Rohbefund,
kein Ergebnis**. Vor dem Weiterreichen an den Nutzer wird mindestens eine
Aussage des Berichts stichprobenartig gegengeprueft - und zwar eine, die der
Agent als geprueft und in Ordnung markiert hat.

**Why:** Zwei parallele Sonnet-Reviews (Regel-Review gegen `.rules/`,
thermo-nuclear Qualitaets-Review) meldeten beide APPROVE mit null Findings fuer
den Referenz-Slice. Der menschliche Review derselben Dateien fand kurz darauf
rund zehn echte Punkte, darunter ein selbstgemachtes TOCTOU-Race in der Naht,
eine Regex-Validierung ohne Fallabdeckung und ein falsch platziertes
Modul-Layout - nichts davon hatten die Agenten erwaehnt. Beim Nachpruefen einer
einzigen ihrer gruenen Zeilen fiel ausserdem ein realer, ungeloester Widerspruch
zwischen `.rules/python/python-data-access.md` und `docs/Draft/BACKEND.md` §0.12
auf, den ein Agent aktiv mit einer erfundenen Begruendung („betrifft Stufe 2")
abgeraeumt hatte.

Zwei Muster in den Berichten waren rueckblickend die Warnsignale: eine
**lueckenlos gruene Pruefmatrix** ueber 50 Zeilen, und ein Pflichtabschnitt
„Zweifelsfaelle", dessen Eintraege der Agent alle selbst wieder mit „kein
Finding" schloss. Ein Zweifel, der sich selbst neutralisiert, ist Zustimmung in
anderer Schrift.

**How to apply:** Bei `Findings: 0` nicht den Bericht weiterreichen, sondern
**eine als gruen gemeldete Regel selbst nachlesen** und gegen den Diff halten;
bevorzugt eine, bei der Regelwerk und Spezifikation auseinanderlaufen koennten.
Den Zweifelsfall-Abschnitt danach beurteilen, ob er echte offene Fragen enthaelt
- ein Abschnitt voller selbst geschlossener Punkte zaehlt als leer. Und die
Grenze klar benennen: Agenten-Reviews ersetzen den menschlichen Review nicht,
sie verkuerzen ihn. Verwandt: [[verify-subagent-progress-claims]],
[[gruenes-gate-ohne-scope-angabe]].
