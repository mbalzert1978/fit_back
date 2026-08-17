# Der Worktree-Wächter entscheidet Fall 2 auch am Zielpfad

**Entschieden am 2026-08-17 um 09:20.**

## Was entschieden wurde

`.claude/hooks/forbid-write-outside-worktree.py` lässt in Fall 2 — Sub-Agent, Arbeitsverzeichnis
im Haupt-Checkout, mindestens ein Worktree registriert — einen Schreibzugriff durch, **wenn das
Ziel in einem von git registrierten Worktree liegt**. Jeder andere Schreibzugriff dieses Falls
bleibt blockiert.

Dabei ist maßgeblich, was `git worktree list --porcelain` meldet, nicht was unter
`.claude/worktrees/` herumliegt. Die Hilfsfunktion `any_worktree_registered` wurde dafür zu
`registered_worktrees` und gibt die Pfade zurück, statt nur deren Existenz zu behaupten — dasselbe
Prinzip, das sie vorher schon in ihrem eigenen Docstring formuliert hat: „a leftover directory is
not an active worktree".

## Warum

Fall 2 entschied ausschließlich aus `agent_id` plus „irgendein Worktree registriert". Der Zielpfad
kam in der Bedingung nicht vor. Ein Schreibzugriff in einen Worktree ist aber `is_relative_to(root)`
— er fiel damit durch bis Fall 2 und wurde blockiert, mit der Meldung „Sub-Agent schreibt in den
Haupt-Checkout", die in diesem Fall schlicht falsch war.

Damit blockierte der Wächter **genau die Handlung, für die die Pipeline Worktrees anlegt**. Er traf
zuerst den Team-Lead, der einen `Task.md`-Brief in einen Worktree schreiben wollte (umgangen per
`Copy-Item`, weil Bash kein Edit/Write ist), und dann den Entwickler-Agenten für Ticket #51, bevor
eine Zeile Code entstanden war.

Der Ausweg, den die Blockmeldung selbst vorschlug — „wechsle zuerst explizit in den zugewiesenen
Worktree" —, ist für einen Sub-Agenten **strukturell nicht erreichbar**:

- Edit/Write melden in der Hook-Nutzlast das **Sitzungs**-Arbeitsverzeichnis. Ein `cd` in einem
  Bash-Aufruf bewegt das nicht.
- In einem über das Agent-Tool gestarteten Thread wird das Arbeitsverzeichnis zwischen den
  Bash-Aufrufen ohnehin zurückgesetzt: `cd <worktree> && pwd` meldet den Worktree, der nächste,
  eigenständige `pwd`-Aufruf wieder den Repo-Root.
- `EnterWorktree(path=…)` verweigert mit „switching is only available to sessions whose working
  directory is inside a worktree of this repository".

Die Annahme aus
[`2026-08-13-0959-worktree-waechter-statt-projektverzeichnis-vergleich.md`](2026-08-13-0959-worktree-waechter-statt-projektverzeichnis-vergleich.md)
(„cwd folgt dem cd", damals live bestätigt) gilt für eine **Sitzung**, die per `cd` in den Worktree
wechselt. Für einen Agenten-Thread gilt sie nicht. Das ist die eigentliche Korrektur: nicht die
Regel war falsch, sondern ihr Geltungsbereich zu weit angenommen.

## Was das nicht ist

**Keine Abschwächung von Fall 2.** Der Vorfall vom 2026-08-07, gegen den Fall 2 gebaut wurde, war
ein Sub-Agent, der **in den Haupt-Checkout** schrieb. Genau das bleibt blockiert. Verifiziert gegen
zehn Fälle:

| Fall | vorher | jetzt |
| --- | --- | --- |
| Sub-Agent → zugewiesener Worktree | BLOCK | **ALLOW** |
| Sub-Agent → Haupt-Checkout `src/` | BLOCK | BLOCK |
| Sub-Agent → Haupt-Checkout `.claude/` | BLOCK | BLOCK |
| Sub-Agent → `.claude/worktrees/` selbst | BLOCK | BLOCK |
| aus Worktree → Haupt-Checkout | BLOCK | BLOCK |
| aus Worktree → fremder Worktree | BLOCK | BLOCK |
| Hauptsitzung → Haupt-Checkout | ALLOW | ALLOW |
| Sub-Agent → Scratchpad | ALLOW | ALLOW |

## Was bewusst offen bleibt

**Ein Sub-Agent darf in einen fremden Worktree schreiben**, nicht nur in den ihm zugewiesenen. Fall
2 kennt die Zuweisung nicht — sie steht nirgends, wo der Hook sie lesen könnte — und kann sie
deshalb nicht prüfen. Fall 1 blockt Worktree-zu-Worktree weiterhin, weil dort das
Arbeitsverzeichnis die Zugehörigkeit verrät.

Das ist hingenommen, nicht übersehen: Der Schaden, gegen den der Wächter gebaut ist, ist die
Verschmutzung des Haupt-Checkouts; zwei Agenten, die sich in ihren Worktrees ins Gehege kommen,
fallen spätestens im PR auf und kosten keinen Vorfall. Wer das schließen will, müsste die Zuweisung
für den Hook sichtbar machen — ein größerer Umbau als der Nutzen rechtfertigt.

## Ausgelöst durch

Die Welle an Map [#40](https://github.com/mbalzert1978/fit_back/issues/40) vom 2026-08-17, Tickets
[#51](https://github.com/mbalzert1978/fit_back/issues/51) und
[#89](https://github.com/mbalzert1978/fit_back/issues/89). Der Entwickler-Agent für #51 hat den
Hook **nicht** umgangen — weder per Heredoc noch per `Set-Content`, `python -c` oder `git apply`,
obwohl das alles funktioniert hätte, weil der Hook nur auf `Edit|Write|NotebookEdit` matcht — und
stattdessen eskaliert. Das ist das gewünschte Verhalten und der Grund, warum der Fehlalarm als
Fehlalarm sichtbar wurde statt als stiller Umweg.

Dass ein blockierender Hook per Bash umgehbar ist, bleibt bestehen und ist hier nicht adressiert.
