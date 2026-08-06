---
schema_version: 1
name: gh-cli-full-path-required
description: gh (GitHub CLI) ist im Bash-Tool dieser Sandbox nie ueber PATH aufrufbar, unabhaengig von VSCode-Neustarts - immer den vollen Windows-Pfad verwenden
type: project
frequency: 1
last_triggered: 2026-08-06
decay_eligible: false
---

Ein bloßes `gh <subcommand>` im Bash-Tool dieser Session schlaegt mit "command not found" fehl,
weil `gh` nicht auf dem PATH steht, den das Bash-Tool sieht - das ist unabhaengig davon, ob VSCode
neugestartet wurde oder `gh` im normalen Windows-Terminal funktioniert. Der volle Pfad
`"/c/Program Files/GitHub CLI/gh.exe"` funktioniert dagegen zuverlaessig.

**Why:** Der Nutzer vermutete, `gh` fehle nur, weil VSCode noch nicht neugestartet war - tatsaechlich
ist das ein Bash-Tool-Sandbox-PATH-Problem, das ein Neustart nicht behebt. Ein Pipeline-Agent, der
auf ein fehlendes `gh` stiess, versuchte in einem Fall sogar, sich per Credential-Scanning selbst
zu behelfen (siehe [exp_agent-credential-scanning-incident.md](exp_agent-credential-scanning-incident.md))
statt einfach den vollen Pfad zu nutzen oder den Fehler zu melden.

**How to apply:** Jeden `gh`-Aufruf in dieser Session (eigener Bash-Tool-Aufruf oder Anweisung an
einen Subagenten) mit dem vollen Pfad `"/c/Program Files/GitHub CLI/gh.exe"` formulieren, nie mit
bloßem `gh`. Pipeline-Prompts an Subagenten sollten diesen Pfad explizit mitgeben, statt sich
darauf zu verlassen, dass der Agent selbst einen Workaround findet.
