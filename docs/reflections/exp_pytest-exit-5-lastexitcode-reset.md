---
schema_version: 1
name: pytest-exit-5-lastexitcode-reset
description: pytest exit 5 (0 Tests) muss toleriert werden UND danach $global:LASTEXITCODE explizit zurueckgesetzt werden
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

`pytest` liefert Exit-Code 5, wenn keine Tests gesammelt wurden — fuer
tooling-only Tickets (die noch keine Testdateien mitbringen) ein legitimer,
gruener Zustand, kein Fehler. In PowerShell reicht es NICHT, den `throw` fuer
diesen Exit-Code einfach zu unterdruecken — `$LASTEXITCODE` bleibt danach `5`
und wird als Exit-Code des gesamten Skript-Prozesses durchgereicht, sofern nicht
explizit `$global:LASTEXITCODE = 0` gesetzt wird.

**Why:** `make.ps1`s `test`-Target wertete Exit-Code 5 zunaechst als Fehler. Der
erste Fix (nur den `throw` bedingt ueberspringen) reichte nicht — CI blieb rot,
weil PowerShell den zuletzt gesetzten `$LASTEXITCODE` weiterhin als
Prozess-Exit-Code verwendet. Details:
[docs/decisions/2026-08-05-1110-ci-nacharbeiten-nach-ticket-0002-merge.md](../decisions/2026-08-05-1110-ci-nacharbeiten-nach-ticket-0002-merge.md).

**How to apply:** Immer wenn ein PowerShell-Skript einen nativen Exit-Code
selektiv toleriert (nicht nur bei pytest), danach explizit
`$global:LASTEXITCODE = 0` setzen und lokal verifizieren (`$LASTEXITCODE` nach
dem Skriptlauf pruefen), nicht nur den fehlenden `throw` als ausreichend annehmen.
