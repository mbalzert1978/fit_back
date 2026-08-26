---
schema_version: 1
name: schweigen-des-typpruefers-ist-kein-freispruch
description: Ein Typpruefer schweigt auch dort, wo er einen Typ nicht aufloesen konnte (`Unknown` ist zu allem zuweisbar) - und sein Gruen deckt nur seine eigene Regelmenge, nicht die des Repos
type: project
frequency: 1
last_triggered: 2026-08-26
decay_eligible: true
---

Zwei Formen falscher Sicherheit bei einem Typpruefer, beide in derselben Sitzung eingetreten:

1. **Er schweigt, weil er nichts weiss.** Loest eine Annotation zu `Unknown` auf, ist sie zu allem
   zuweisbar — die Zeile wird nie beanstandet, egal wie falsch sie ist.
2. **Sein Gruen ist nicht das Ende der Pruefung.** Eine typkorrekte Loesung kann gegen eine Regel
   verstossen, die ein anderes Gate haelt.

**Why:** In `db_schemas.py` war `Column[Uuid]` genauso falsch wie die gemeldeten Nachbarzeilen —
`Column` ist ueber den *Python*-Wert generisch, nicht ueber den SQL-Typ —, wurde aber nie gemeldet,
weil `Uuid` einen constrained TypeVar traegt, den `ty` aus der nackten Klassenreferenz nicht
aufloesen kann: es ergibt `Column[Unknown]`. Die Zeile stand nur deshalb in der Korrektur, weil in
einer Datei nicht zwei Prinzipien stehen sollten. Und in Welle 4 lieferte ein Subagent eine
typkorrekte, `ty`-gruene Loesung, deren zweiarmiger `match` `tests/test_match_exhaustiveness.py`
brach (der letzte Zweig endete nicht laut) — dieselbe Aufgabe loeste eine Guard-Klausel ohne
Regelverstoss. Hergang: `docs/decisions/2026-08-25-1500-typechecker-ty.md`.

**How to apply:** Bei jeder Aenderung an generischen Annotationen fremder Bibliotheken den
tatsaechlich abgeleiteten Typ ausgeben lassen (`reveal_type`), statt aus dem Schweigen auf
Richtigkeit zu schliessen — insbesondere bei constrained TypeVars und bei allem, was aus Stubs
kommt. Steht in einer Datei eine Zeile derselben Bauart wie eine gemeldete, gilt der Befund fuer
beide. Und nach jedem gruenen Typpruefer die **uebrigen** Gates fahren, bevor etwas als fertig
gemeldet wird. Verwandt:
[exp_gruenes-gate-ohne-scope-angabe.md](exp_gruenes-gate-ohne-scope-angabe.md) (dort: ein Gate, das
seinen Pruefumfang verschweigt).
