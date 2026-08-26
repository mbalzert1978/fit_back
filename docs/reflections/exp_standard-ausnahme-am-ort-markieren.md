---
schema_version: 1
name: standard-ausnahme-am-ort-markieren
description: Muss ein Coding-Standard an genau einer Stelle gebrochen werden, wird nicht die Regel geaendert - die Stelle markiert sich selbst als Ausnahme, mit dem Grund, der nur dort zutrifft
type: feedback
frequency: 1
last_triggered: 2026-08-26
decay_eligible: true
---

Wenn eine Regel aus `.rules/` an einer einzelnen Stelle nachweislich nicht einloesbar ist, ist die
Antwort **nicht**, die Regel aufzuweichen oder still davon abzuweichen. Die Regel bleibt
unveraendert gueltig; die Abweichung wird **am Ort** dokumentiert — im Docstring der Funktion, mit
dem Grund, der genau dort zutrifft, und mit dem Satz, dass die Stelle keine Vorlage ist.

**Why:** In `_fault_of` (`src/api/exception_handlers.py`) matcht der Code sechs
Pydantic-Fehlertypen. `error["type"]` ist ein `str`, und `str` hat keine geschlossene Fallmenge —
nach sechs Literalen bleibt ein Rest, die `Never`-Zusage von `assert_never` ist dort statisch nicht
einloesbar, und `ty` meldet das zu Recht. `.rules/python/python-error-handling.md` schreibt
`assert_never` aber ausdruecklich als das *eine* Muster vor, „ohne Abwaegung an der Schreibstelle",
und hat den selbstgebauten Wurf schon einmal geprueft und verworfen. Auf die Frage, ob die Regel
nachzuziehen sei, entschied der Nutzer: *„wir behalten den Wurf, aber die `.rules` sind weiterhin
korrekt — dies ist eine Ausnahme, nicht die Regel, und das wird im Docstring der Funktion auch
kommuniziert."*

**How to apply:** Sobald ein Standard an einer Stelle nicht traegt, erst pruefen, ob der Grund
**lokal** ist (hier: offene Fallmenge eines Fremdtyps) oder **allgemein** (dann gehoert die Regel
tatsaechlich geaendert, per Decision-Doc). Ist er lokal: Code so lassen, wie er richtig ist, und in
den Docstring drei Dinge schreiben — (1) die Regel gilt unveraendert, (2) der Grund, der nur hier
zutrifft, (3) „wer das als Vorlage nimmt, hat die Stelle missverstanden". Nicht das Muster ist das
Neue, sondern die Ausnahmebedingung. Ein `# noqa`-artiger Kommentar ohne diese drei Teile ist zu
wenig: der naechste Leser haelt ihn fuer ein zweites erlaubtes Muster.
