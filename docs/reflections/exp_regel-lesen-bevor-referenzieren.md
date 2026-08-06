---
schema_version: 1
name: regel-lesen-bevor-referenzieren
description: Eine Regel-Datei, auf die ich einen Agenten verweise, muss ich selbst gelesen haben - ein Verweis auf ungelesene Regeln ist Dekoration und laesst meine eigenen Vermutungen unbemerkt an ihre Stelle treten
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: false
---

Bevor ich in einem Brief, einem Gate oder einer Bewertung auf eine Regel-Datei verweise, lese ich
sie vollstaendig. Ein Verweis auf eine ungelesene Datei ist kein Qualitaetsmerkmal des Prompts,
sondern eine Luecke, die sich unbemerkt mit meinen eigenen Annahmen fuellt.

**Why:** Ich habe ueber mehrere Wellen hinweg Agenten auf `.rules/python/python-feature-slices.md`
verwiesen, ohne die Datei je gelesen zu haben, und parallel eigene Vorstellungen als konkrete
Anweisung mitgegeben. Erst als der Nutzer mich direkt fragte („ist dir klar wie du deine agenten
beauftragen musst"), habe ich sie geoeffnet — und dort standen die zentralen Konstrukte
(Handler/Adapter/Mapper-Rollentrennung, `Result[T, E]` mit einem flachen Fehlertyp, keine rohen
Primitive in der Domaene, Tests nur ueber die public Test-API), die in jedem einzelnen PR verletzt
worden waren. Der Verweis hat die Verstoesse nicht verhindert, weil er nie mit Inhalt gedeckt war.

**How to apply:** Beim ersten Kontakt mit einem Repo bzw. vor dem ersten Brief einer Welle: den in
`CLAUDE.md`/`README` benannten Leseweg der Regeln tatsaechlich abarbeiten (hier:
`.rules/python/README.md` und die darin gelistete Reihenfolge). Wenn ich eine Regel-Datei
referenziere und nicht in eigenen Worten sagen kann, was sie fordert, habe ich sie nicht gelesen —
dann erst lesen, dann briefen. Gleiches gilt, bevor ich ein Gate-Urteil als korrekt akzeptiere.
