---
schema_version: 1
name: powershell-set-content-bom
description: PowerShell 5.1 "Set-Content -Encoding utf8" schreibt eine BOM, die TOML/JSON-Parser (uv, ruff) zum Scheitern bringt
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

`Set-Content -Encoding utf8` (und `Out-File -Encoding utf8`) schreiben in
Windows PowerShell 5.1 UTF-8 **mit BOM**. Tools wie `uv`/`ruff`, die TOML-Dateien
parsen, brechen dann mit kryptischen Fehlern wie „Invalid statement (at line 1,
column 1)" ab — der eigentliche Dateiinhalt ist korrekt, nur die BOM stoert.
BOM-freies Schreiben braucht `[System.Text.UTF8Encoding]::new($false)` +
`[System.IO.File]::WriteAllText(...)` statt `Set-Content`/`Out-File`.

**Why:** Beim manuellen Aufloesen eines Merge-Konflikts in `pyproject.toml`
(Ticket-0004-Branch) per PowerShell fuehrte `Set-Content -Encoding utf8` zu
genau diesem Fehler — `uv lock`/`uv sync`/`ruff` konnten die Datei danach nicht
mehr lesen, bis die BOM per `[System.IO.File]::WriteAllText` mit
`UTF8Encoding($false)` entfernt wurde.

**How to apply:** Bei jedem PowerShell-Schreibzugriff auf eine Datei, die von
einem externen Tool (uv, ruff, git, JSON/TOML-Parser) gelesen wird, `WriteAllText`
mit `UTF8Encoding($false)` statt `Set-Content -Encoding utf8` verwenden — oder,
wo moeglich, gleich das Edit/Write-Tool statt PowerShell nutzen (das schreibt
ohnehin ohne BOM).
