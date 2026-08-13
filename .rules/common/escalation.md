# Eskalation bei Unschlüssigkeit

## Die Regel

**Wer unschlüssig ist, rät nicht.** Eine geratene Annahme ist im Ergebnis nicht von einer
getroffenen Entscheidung zu unterscheiden — sie sieht fertig aus und trägt nicht.

## Mit Mensch in der Schleife

Fragen, bevor entschieden wird. Eine kurze Rückfrage kostet weniger als eine falsche Annahme, die
erst drei Schritte später auffällt.

## Ohne Mensch in der Schleife

Ein Agent im Worktree, in der Ticket-Pipeline oder im Hintergrund hat niemanden zu fragen. Für ihn
gilt:

1. **Anhalten**, nicht annehmen.
2. Die Unschlüssigkeit benennen — was genau offen ist und welche Antworten in Frage kommen.
3. Den beauftragenden Agenten **auffordern, die Frage an den Menschen zu dirigieren**.

## Die Kette nach oben

Jede Ebene entscheidet nur, was sie aus **eigenem Kontext ohne Raten** entscheiden kann. Reicht ihr
Kontext nicht, reicht sie weiter nach oben — bis ein Mensch antwortet. Eine Ebene höher zu sitzen
erlaubt keine Annahme, die eine Ebene tiefer verboten war.

## Belege

- [`exp_agent-credential-scanning-incident.md`](../../docs/reflections/exp_agent-credential-scanning-incident.md)
  — ein Subagent, dem `gh` fehlte, suchte selbst nach Zugangsdaten, statt anzuhalten und zu melden.
- [`exp_gruenes-gate-ohne-scope-angabe.md`](../../docs/reflections/exp_gruenes-gate-ohne-scope-angabe.md)
  — ohne ausgewiesenen Prüfumfang ist „nichts gefunden" nicht von „nichts geprüft" zu unterscheiden.
