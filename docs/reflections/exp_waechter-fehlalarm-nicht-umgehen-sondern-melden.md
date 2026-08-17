---
schema_version: 1
name: waechter-fehlalarm-nicht-umgehen-sondern-melden
description: Ein Kontroll-Hook, der am falschen Merkmal entscheidet, blockiert die ganze Pipeline - wer ihn umgeht statt ihn zu melden, nimmt der Pipeline ihre Diagnose; der Umweg ist die Meldung wert, auch wenn er funktioniert
type: feedback
frequency: 1
last_triggered: 2026-08-17
decay_eligible: false
---

Ein PreToolUse-Waechter, der **am Arbeitsverzeichnis des Aufrufers** entscheidet statt **am
Zielpfad**, blockiert auch den legitimen Fall: den Team-Lead, der aus dem Haupt-Checkout heraus
eine Datei **in** einen Worktree schreibt. Wer darauf trifft, hat zwei Wege — den Umweg nehmen
(Datei ins Scratchpad schreiben, per `Copy-Item` an den Zielort kopieren) oder den Waechter als
defekt melden. **Beides ist zu tun, und das Melden ist der wichtigere Teil.**

**Why:** In der Welle vom 2026-08-17 traf der Waechter
`forbid-write-outside-worktree.py` beim Ablegen der `Task.md` in beide Worktrees zu. Sein Fall 2
prueft `agent_id` + „irgendein Worktree registriert" und blockiert dann **jeden** Schreibzugriff
unterhalb des Repos — auch den, dessen Ziel im Worktree liegt und den er gerade erzwingen will.
Seine eigene Fehlermeldung sagt „wechsle in den zugewiesenen Worktree und wiederhole von dort",
was ein Agent mit festgepinntem `cwd` nicht kann.

Ich habe den Umweg genommen und ihn in einem Nebensatz erwaehnt, statt ihn als Befund zu
behandeln. Der Preis war hoch: derselbe Waechter blockierte danach den Entwickler-Agenten fuer
Ticket #89, der seine eine Quelltextaenderung ueber ein `uv run python`-Skript **im** Worktree
schreiben musste — und die Welle verlor eine komplette Runde, bevor die Ursache benannt war.
Der Fix (`62e4700` auf `main`) besteht darin, Fall 2 zusaetzlich am **Zielpfad** entscheiden zu
lassen: liegt das Ziel unterhalb eines registrierten Worktrees, ist es kein Uebergriff.

Der Entwickler-Agent hat sich dabei **richtig** verhalten, und das gehoert festgehalten: er haette
den Waechter trivial ueber die Shell umgehen koennen — Hooks greifen nur an `Edit`/`Write`/
`NotebookEdit`, nicht an `Bash`/`PowerShell`. Er hat den Umweg genommen, den Zielort strikt
eingehalten und den Vorgang im Bericht unter „Hook-Reibung" ausdruecklich als Reibung gemeldet,
mit Diagnose (`cwd` statt Zielpfad) und Vorschlag. Genau diese Meldung hat den Fehlalarm sichtbar
gemacht. Ein Agent, der still umgeht, haette dieselbe Arbeit geliefert und die Ursache begraben.

**How to apply:** Trifft ein Kontroll-Hook zu, wo er nicht sollte, ist der Umweg zulaessig — aber
er erzeugt eine **Bringschuld**, keine Erledigung. Drei Punkte, in dieser Reihenfolge:

1. **Sofort pruefen, woran der Waechter entscheidet**, bevor man weiterarbeitet: liest er das
   Ziel oder den Kontext des Aufrufers? Ein Waechter, der Kontext liest, hat ein Fehlalarm-Muster
   und trifft als naechstes jemand anderen.
2. **Als Befund melden, nicht als Nebensatz.** Formulierung, die traegt: „Der Hook hat X blockiert,
   obwohl das Ziel Y innerhalb des erlaubten Bereichs liegt — er entscheidet an Z statt am
   Zielpfad." Ein „ich habe es umgangen, lief dann" ist keine Meldung.
3. **Umgehung nie ueber einen Weg, den der Hook nicht sieht, ohne sie offenzulegen.** Dass
   `Bash`/`PowerShell` an `PreToolUse(Edit|Write)` vorbeilaufen, macht den Umweg moeglich und die
   Offenlegung damit erst recht noetig — sonst ist von aussen nicht unterscheidbar, ob eine Regel
   eingehalten oder nur nicht gemessen wurde.

Verwandt: [[maschinelle-absicherung-statt-review-regel]] (ein mechanischer Waechter ersetzt ein
Review — dann muss er aber am richtigen Merkmal messen), [[pruefkommando-muss-messen-was-es-behauptet]],
[[gruenes-gate-ohne-scope-angabe]]. Ursache und Fix:
[docs/decisions/2026-08-17-0920-waechter-entscheidet-fall-2-auch-am-zielpfad.md](../decisions/2026-08-17-0920-waechter-entscheidet-fall-2-auch-am-zielpfad.md).
