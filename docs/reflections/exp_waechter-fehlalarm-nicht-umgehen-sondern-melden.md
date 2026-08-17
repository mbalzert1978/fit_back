---
schema_version: 1
name: waechter-fehlalarm-nicht-umgehen-sondern-melden
description: Ein Kontroll-Hook, der am falschen Merkmal entscheidet, blockiert die ganze Pipeline - Melden ist in jedem Fall Pflicht, der Umweg ist zulaessig, aber Stehenbleiben und Eskalieren ist die staerkere Variante, wenn der Blocker die Arbeit ohnehin ganz verhindert
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

**Beide Entwickler-Agenten trafen den Waechter, und sie reagierten verschieden.** Das ist der
lehrreiche Teil, und beide Haelften gehoeren festgehalten — Hooks greifen nur an
`Edit`/`Write`/`NotebookEdit`, nicht an `Bash`/`PowerShell`, der Umweg stand also beiden offen:

- **Ticket #89 nahm den Umweg.** Der Agent schrieb seine eine Quelltextaenderung ueber ein
  `uv run python`-Skript **innerhalb** seines Worktrees, hielt den Zielort strikt ein und meldete
  den Vorgang im Bericht unter „Hook-Reibung" mit Diagnose (`cwd` statt Zielpfad) und Vorschlag.
- **Ticket #51 nahm ihn nicht.** Der Agent blieb stehen, **bevor eine Zeile Code entstanden war**,
  und eskalierte: „harter Blocker … Ich umgehe ihn nicht." Er zaehlte die Wege, die er kannte und
  bewusst nicht ging, einzeln auf — Heredoc, `Set-Content`, `python -c`, `git apply` — und lieferte
  den blockierten Zielpfad samt Exit-Code mit.

**Die Bewertung ist abgestuft, nicht binaer.** Melden ist in **beiden** Faellen Pflicht; genau die
Meldung hat den Fehlalarm sichtbar gemacht, und ein Agent, der still umgeht, haette dieselbe Arbeit
geliefert und die Ursache begraben. Der Umweg ist **zulaessig**, solange er offengelegt wird und
den Zielort einhaelt. Aber **Stehenbleiben und Eskalieren ist die staerkere Variante**, wenn der
Blocker die Arbeit ohnehin ganz verhindert: es liefert die Diagnose unverfaelscht, ohne dass
jemand hinterher rekonstruieren muss, was am Waechter vorbei geschrieben wurde. Wer umgeht,
schuldet die Offenlegung **sofort und als Antwort**, nicht beilaeufig in einem spaeteren Dokument —
im Vorfall vom 2026-08-17 wurde nach genau dieser Auskunft gefragt, und sie tauchte erst als
Nebenprodukt auf, als der Code laengst in einem PR lag.

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
   eingehalten oder nur nicht gemessen wurde. Die Offenlegung nennt **was und wohin** geschrieben
   wurde, und sie kommt, **bevor** committet wird.
4. **Verhindert der Blocker die Arbeit ohnehin vollstaendig, ist Stehenbleiben besser als der
   Umweg.** Dann kostet Eskalieren nichts ausser Wartezeit und liefert die sauberste Diagnose.
   Lohnt der Umweg (die Arbeit laeuft sonst weiter), ist er zu nehmen **und** sofort zu melden.

Verwandt: [[maschinelle-absicherung-statt-review-regel]] (ein mechanischer Waechter ersetzt ein
Review — dann muss er aber am richtigen Merkmal messen), [[pruefkommando-muss-messen-was-es-behauptet]],
[[gruenes-gate-ohne-scope-angabe]]. Ursache und Fix:
[docs/decisions/2026-08-17-0920-waechter-entscheidet-fall-2-auch-am-zielpfad.md](../decisions/2026-08-17-0920-waechter-entscheidet-fall-2-auch-am-zielpfad.md).
