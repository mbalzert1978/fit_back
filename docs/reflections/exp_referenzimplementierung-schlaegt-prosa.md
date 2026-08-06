---
schema_version: 1
name: referenzimplementierung-schlaegt-prosa
description: Solange kein implementiertes Referenz-Feature existiert, erfindet jeder Agent die Zielform neu und produziert dieselbe Klasse Strukturfehler - eine Referenzimplementierung ist wirksamer als jede noch so genaue Regel-Prosa
type: project
frequency: 1
last_triggered: 2026-08-06
decay_eligible: false
---

Eine Architektur-Regel in Prosa reicht nicht aus, damit Agenten sie treffen. Solange kein
gebautes, gemergtes Referenz-Feature existiert, auf das der Brief und die Review-Gates zeigen
koennen, rekonstruiert jeder Agent die Zielform aus der Beschreibung neu — und trifft sie
systematisch anders.

**Why:** In `fit_back` hatte M0 (Tickets 0001-0010) ausschliesslich Infrastruktur gebaut, also
existierte **kein einziges Feature-Slice**.
`.claude/skills/review-against-rules/config.json` vermerkte das sogar selbst
(`reference_implementation` bewusst nicht gesetzt, „es existiert noch kein implementiertes Feature
in diesem frischen Repo"), und `.rules/python/python-feature-slices.md` sagte in ihrer eigenen
Kopfnotiz, sie bleibe generisch, bis ein Referenz-Feature existiert. Ergebnis: **jeder** M0-PR
zeigte dieselben Verstoesse (invertierte Abhaengigkeitsrichtung, Framework-Importe in der Domaene,
Exceptions statt `Result`, kein Pattern Matching, Tests am falschen Ort) — nicht weil die Agenten
schlecht waren, sondern weil es nichts gab, woran sie sich ausrichten konnten. Zum Vergleich:
das Schwesterprojekt `dhcp-mac-verwaltung` hat mit `Features.MacSuche` genau so ein Referenz-Feature
inklusive Test-API und Specs, und dort ist die Form ueber alle Features hinweg konsistent.

**How to apply:** Bei einem Repo ohne Referenzimplementierung: das **erste** Feature-Slice bewusst
als Referenz bauen (hier: Ticket 0011 `register_user`), es besonders sorgfaeltig reviewen, und
danach sofort `reference_implementation` in `review-against-rules/config.json` sowie die
Regel-Dateien darauf zeigen lassen. Bis dahin muss jeder Brief die Zielform explizit mittragen —
das ist teuer und fehleranfaellig, aber die einzige Bruecke. Regel-Prosa ohne Beispiel nie als
ausreichende Anweisung behandeln.
