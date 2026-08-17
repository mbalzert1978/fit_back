---
schema_version: 1
name: startquittung-ist-kein-fortschritt
description: Ein Hintergrund-Agent, den ein Subagent startet, wird an dessen Turn-Grenze abgeraeumt - und die Erfolgsquittung des Tools belegt nur den Start, nie die Arbeit; Fortschritt wird an Git gemessen, nicht an Tool-Antworten
type: project
frequency: 1
last_triggered: 2026-08-17
decay_eligible: false
---

Zwei Regeln, die derselbe Vorfall erzeugt hat:

1. **Wer selbst Subagent ist, startet Entwickler-Agenten im Vordergrund.** Ein mit
   `run_in_background: true` gestartetes Kind eines Subagenten ueberlebt dessen Turn-Grenze nicht
   zuverlaessig. Es hinterlaesst eine angelegte, **null Byte grosse** Transkriptdatei und meldet
   nie etwas.
2. **Die Startquittung eines Tools ist kein Fortschrittsbeleg.** `Async agent launched
   successfully` belegt den Start, nicht die Arbeit. `Message queued for delivery` belegt die
   Zustellung in eine Queue, nicht die Existenz eines lebenden Empfaengers.

**Why:** In der Welle vom 2026-08-17 wurden beide Entwickler-Agenten als Hintergrund-Kinder
gestartet, die Quittung als Erfolg gelesen und der Turn beendet. Beide Transkripte blieben bei
0 Byte. Ich meldete zweimal „warte auf die Agenten", waehrend nichts lief, und schickte
zwischendurch eine Korrektur (ein vergessenes fuenftes Gate) an zwei Empfaenger, die es nicht
mehr gab — auch das mit einer Erfolgsquittung bestaetigt. Zwei Runden verloren; aufgefallen ist
es dem Stakeholder, nicht mir, obwohl `git -C <worktree> log --oneline main..HEAD` die ganze Zeit
leer war und ich es selbst mehrfach ausgefuehrt hatte, ohne die Konsequenz zu ziehen.

Bitter daran: derselbe Grundsatz stand bereits in beiden Briefs, die ich fuer diese Welle
geschrieben hatte („Behaupte kein gruenes Gate, das du nicht gefahren hast"). Ich habe ihn an die
Agenten adressiert und auf mich selbst nicht angewandt. Die Diagnose war ausserdem nur halb
richtig — der Hintergrund-Agent fuer #89 lieferte spaeter doch, der fuer #51 nie; „abgeraeumt"
beschreibt also eine Tendenz, keine Gesetzmaessigkeit. Umso mehr zaehlt die Messung statt der
Vermutung.

**How to apply:**

- Entwickler-Agenten in Worktrees **im Vordergrund** starten (`run_in_background: false`), auch
  mehrere gleichzeitig in **einer** Nachricht — das laeuft nebenlaeufig und liefert die Berichte
  echt zurueck. Hintergrund nur fuer Arbeit, deren Ergebnis man nicht braucht.
- Fortschritt **nie** aus Tool-Quittungen oder Agentenberichten ableiten. Der Beleg ist
  `git -C <worktree> log --oneline main..HEAD` und `git -C <worktree> status --short`. Steht dort
  nichts, ist nichts passiert — unabhaengig davon, was gemeldet wurde.
- Frueh-Diagnose ohne Kontext zu verbrennen: die Groesse der Transkriptdatei des Agenten. **0 Byte
  heisst „kein einziger Tool-Aufruf"**, also gestartet und sofort tot. Die Datei selbst nicht
  lesen — sie ist das vollstaendige JSONL-Transkript und sprengt den Kontext.
- Bevor „ich warte" gemeldet wird, einmal messen. „Warten" ist eine Aussage ueber die Realitaet
  und braucht denselben Beleg wie jede andere.

Verwandt: [[verify-subagent-progress-claims]], [[hintergrund-agent-delegiert-nicht-weiter]],
[[pruefkommando-muss-messen-was-es-behauptet]], [[gruenes-gate-ohne-scope-angabe]].
