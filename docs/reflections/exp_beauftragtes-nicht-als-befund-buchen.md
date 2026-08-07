---
schema_version: 1
name: beauftragtes-nicht-als-befund-buchen
description: Bevor eine Agenten-Aenderung als "out of scope" oder "Regression" gemeldet wird, pruefen ob der Nutzer sie beauftragt hat - der Auftrag steht oft in keinem Artefakt, das dem Reviewer vorliegt
type: feedback
frequency: 1
last_triggered: 2026-08-07
decay_eligible: true
---

Eine Aenderung, die im Diff wie Eigeninitiative des Agenten aussieht, kann eine direkte Anweisung
des Nutzers sein. Bevor sie als „out of scope" oder „Regression" gemeldet wird: pruefen, ob sie
beauftragt war — und wenn sich das aus `Task.md`, Ticket und Bericht nicht ergibt, **fragen statt
buchen**.

**Why:** Bei Ticket 0048 ersetzte der Agent vier `# noqa: ARG002` durch Umbenennen der Parameter
auf `_`. Ich habe das als Regression und Verstoss gegen „keine fachliche Aenderung" gemeldet,
begruendet mit einer Asymmetrie zwischen den beiden Armen von `Result[T, E]`. Der Nutzer hatte
die Umbenennung selbst beauftragt; sie stand in keinem Artefakt, das ich hatte. Meine
Nachpruefung ergab ausserdem, dass `.rules/python/` nichts dagegen sagt und kein einziger
Keyword-Aufruf auf diese Methoden existiert — der Befund war theoretisch. Uebrig blieb ein
brauchbarer Rest (der Positional-only-Marker `/`), aber als Angebot, nicht als Blockade.

**How to apply:** Beim Lesen eines Agenten-Diffs zwei Fragen trennen: „ist das falsch?" und „ist
das ungefragt?". Fuer die zweite reicht der Diff nicht — der Auftrag kann muendlich ergangen
sein. Formulierungen wie „out of scope", „Regression", „eigenmaechtig" also erst verwenden,
nachdem der Auftragsweg geprueft ist; sonst als offene Frage stellen. Und bei einem Befund, der
nur konstruiert auftreten kann, vor dem Melden die Gegenprobe fahren (gibt es den Aufruf
ueberhaupt? sagt eine Regel etwas dazu?) — haelt er ihr nicht stand, wird er als Vorschlag
formuliert, nicht als Fehler. Verwandt: [[gate-finding-gegen-die-spezifikation-halten]],
[[pruefkommando-muss-messen-was-es-behauptet]].
