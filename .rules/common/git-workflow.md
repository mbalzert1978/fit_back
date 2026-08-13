# Git-Workflow

## Format der Commit-Nachricht

```text
<typ>: <beschreibung>

<optionaler Rumpf>
```

Typen: feat, fix, refactor, docs, test, chore, perf, ci

Hinweis: Die Attribution ist global über `~/.claude/settings.json` abgeschaltet.

## Pull Requests

Beim Erstellen eines PR:

1. Die vollständige Commit-Historie ansehen, nicht nur den letzten Commit
2. `git diff <basis-branch>...HEAD` nutzen, um alle Änderungen zu sehen
3. Eine aussagekräftige Zusammenfassung schreiben
4. Einen Testplan mit offenen Punkten beilegen
5. Bei einem neuen Branch mit `-u` pushen

## Worktrees: nur auf ausdrückliche Bitte

Keinen Git-Worktree anlegen, solange der Nutzer nicht ausdrücklich darum bittet. Sagt jemand „in
einem eigenen Branch", ohne „Worktree" zu sagen, ist ein Branch im Haupt-Checkout gemeint
(`git checkout -b <name>`) — die Wahl zwischen beidem gehört dem Nutzer, nicht einer Voreinstellung.

Ein Worktree legt das Ergebnis in ein Verzeichnis, in dem der Nutzer nicht arbeitet und aus dem es
danach wieder herausgeholt oder gemergt werden muss — nützlich für unbeaufsichtigte Läufe und für
mehrere Agenten parallel, unnötiger Aufwand in einer interaktiven Sitzung. Stellt sich ein Worktree
nachträglich als gewünscht heraus, wird das dafür vorgesehene Projektwerkzeug benutzt statt eines
rohen `git worktree add`, damit der neue Worktree denselben lokalen Projektkontext bekommt wie das
Haupt-Checkout (Skills, Settings, Doku). Bei echter Unschlüssigkeit wird gefragt, nicht entschieden
(siehe [escalation.md](./escalation.md)).
