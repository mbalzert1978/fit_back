---
schema_version: 1
name: alembic-ini-path-separator-windows
description: alembic.ini path_separator = os loest sich zu os.pathsep auf (";" unter Windows, ":" unter Linux) - bei einer mit ":" authored version_locations-Liste bricht das lokale Windows-Ausfuehrung still, ohne Fehler
type: project
frequency: 1
last_triggered: 2026-08-06
decay_eligible: false
---

`path_separator = os` in `alembic.ini` verwendet `os.pathsep` zum Splitten von
`version_locations` - das ist `":"` unter Linux/macOS, aber `";"` unter Windows. Ist
`version_locations` selbst mit `":"` als Trenner geschrieben (der uebliche, in Tutorials gezeigte
Stil), parst Alembic unter Windows die gesamte Liste als EINEN einzigen, nicht-existenten Pfad -
das Ergebnis ist eine leere `version_locations`-Liste, `alembic heads`/`history` liefern
kommentarlos nichts zurueck, und `alembic upgrade heads` laeuft mit Exit-Code 0 durch, OHNE auch
nur eine Migration anzuwenden.

**Why:** In dieser Session lief `./make.ps1 test` lokal unter Windows, die Testcontainers-Fixture
rief `alembic upgrade heads` erfolgreich (Exit 0) auf, aber die Test-DB blieb ohne Schemas -
`test_alembic_migration_applied` schlug mit "Missing schemas: {alle 7}" fehl. `uv run alembic
heads` zeigte lokal buchstaeblich nichts an. In CI (Linux) war das Problem nie sichtbar, weil dort
`":"` == `os.pathsep` zufaellig uebereinstimmt - der Bug war rein Windows-lokal und dadurch lange
unbemerkt (in einer frueheren Session bereits als Verdacht notiert, aber nicht behoben). Siehe auch
[exp_alembic-multi-schema-pitfalls.md](exp_alembic-multi-schema-pitfalls.md) fuer die anderen
Alembic-Multi-Schema-Fallstricke in diesem Repo.

**How to apply:** Wird `version_locations`/`prepend_sys_path` in einer `alembic.ini` mit einem
festen Zeichen (z. B. `":"`) als Trenner geschrieben, muss `path_separator` explizit auf genau
dieses Zeichen gesetzt werden (`path_separator = :`), NIE auf `os` - `os` ist nur korrekt, wenn man
zusaetzlich sicherstellt, dass die Liste selbst plattformabhaengig mit dem jeweils richtigen
Trenner erzeugt wird. Bei jedem "Migration lief scheinbar durch, aber nichts hat sich geaendert"
zuerst `alembic heads`/`alembic history` direkt pruefen, nicht nur den Exit-Code der Migration.
