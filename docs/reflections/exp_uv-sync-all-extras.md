---
schema_version: 1
name: uv-sync-all-extras
description: uv sync installiert optional-dependencies-Gruppen nicht automatisch - CI und lokales Setup brauchen --all-extras
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

`uv sync` installiert Pakete unter `[project.optional-dependencies].<gruppe>`
(z. B. `dev`) NICHT automatisch. Jeder CI-Workflow und jedes lokale Setup-Target
in diesem Repo muss `uv sync --all-extras` verwenden, nie bloßes `uv sync`.

**Why:** `ruff`/`import-linter`/`pytest` waren als `dev`-Extra deklariert; CI und
`make.ps1 install` liefen mit bloßem `uv sync` faktisch ohne diese Tools, obwohl
die Konfiguration existierte — `ruff` war schlicht nicht auf PATH. Details:
[docs/decisions/2026-08-05-1110-ci-nacharbeiten-nach-ticket-0002-merge.md](../decisions/2026-08-05-1110-ci-nacharbeiten-nach-ticket-0002-merge.md).

**How to apply:** Bei jedem neuen `uv sync`-Aufruf in `.github/workflows/*.yml`,
`make.ps1` oder Setup-Dokumentation pruefen, ob optional-dependencies existieren
und `--all-extras` gesetzt ist.
