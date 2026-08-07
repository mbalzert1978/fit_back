---
schema_version: 1
name: lint-fix-kann-bedeutung-kippen
description: Eine mechanisch korrekte Lint-Korrektur kann den gerenderten Text still veraendern - bei Strings und Docstrings das Ergebnis pruefen, nicht nur das gruene Gate
type: feedback
frequency: 1
last_triggered: 2026-08-07
decay_eligible: false
---

Eine Aenderung, die nur eine Lint-Regel bedienen soll, wird bei **Strings und Docstrings am
gerenderten Ergebnis** geprueft, nicht am gruenen Linter. Gruen heisst „die Regel ist
erfuellt", nicht „der Text sagt noch dasselbe".

**Why:** In Ticket 0048 verlangte `D301` einen Raw-String, sobald ein Backslash im Docstring
steht. Der Agent setzte den `r`-Praefix vor
`src/contexts/identity/domain/value_objects/email.py:59` — korrekt — zog aber die vorhandene
Escape-Sequenz nicht mit. Der Text zeigte den Header-Injection-Vektor vorher als
`opfer@example.com\nBcc: ...`; im Raw-String rendert dieselbe Quelle als zwei Backslashes.
`ruff check`, `ruff format`, `lint-imports` und 280 Tests waren dabei durchgehend gruen — kein
Gate konnte das sehen, weil kein Gate Docstrings rendert. Gefunden hat es ein Review-Agent,
allerdings mit falscher Begruendung („`r`-Praefix ueberfluessig, kein Backslash vorhanden"):
der Praefix war noetig, die Escape-Sequenz war das Problem.

**How to apply:** Bei jeder Lint-Korrektur an einem String-Literal oder Docstring — besonders
`D301` (Raw-String), `D400`/`D415` (Satzzeichen), `RUF001`/`RUF002` (Unicode-Homoglyphen) — den
Wert danach ausgeben lassen statt ihn zu lesen: `python -c "...; print(repr(obj.__doc__))"`.
`repr` verdoppelt jeden einzelnen Backslash, also ist `\\n` in der `repr`-Ausgabe genau ein
Backslash im String — wer das verwechselt, misst erneut falsch. Dasselbe Muster bei
`D400`/`D415`: ein angehaengter Punkt hinter einem Fragezeichen (`?.`) erfuellt die Regel und
ist trotzdem kein Deutsch. Verwandt: [[pruefkommando-muss-messen-was-es-behauptet]],
[[maschinelle-absicherung-statt-review-regel]].
