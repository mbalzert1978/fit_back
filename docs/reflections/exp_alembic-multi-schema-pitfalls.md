---
schema_version: 1
name: alembic-multi-schema-pitfalls
description: In diesem Repos Multi-Schema-Alembic-Layout (7 Schemas ueber version_locations) muessen Revision-IDs global eindeutig sein und "alembic upgrade heads" (Plural) statt "head" verwendet werden
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

Dieses Repo hat 7 unabhaengige Schema-Branches (identity, catalog, diary, recipes, goals,
health_sync, shared_kernel), jeder mit eigenem Alembic-Head. Zwei Fallstricke, die erst beim
allerersten echten Migrationslauf (Ticket 0009) sichtbar wurden:

1. Jede Schema-Wurzel-Migration nutzte woertlich `revision = "001"` - gueltig aussehend pro
   Ordner, aber ungueltig fuer Alembics `ScriptDirectory`, die ueber ALLE `version_locations`
   hinweg global eindeutige Revision-IDs verlangt, unabhaengig von `branch_labels`
   ("Revision 001 is present more than once" / "overlaps with other requested revisions").
2. `alembic upgrade head` (Singular) schlaegt mit "Multiple head revisions are present" fehl,
   sobald mehr als ein unabhaengiger Branch existiert - es braucht `alembic upgrade heads`
   (Plural), um alle Branches gemeinsam anzuwenden.

**Why:** Ticket 0003 (Alembic-Grundgeruest) war tooling-only ohne Tests, daher blieb beides
latent, bis Ticket 0009s testcontainers-Fixture zum ersten Mal echt gegen eine Live-DB migrierte.
Gefixt durch `<schema>_001`-Praefixe auf allen Revision-IDs sowie `heads` statt `head` in
`make.ps1` und der Test-Fixture.
**How to apply:** Bei jeder neuen Root-Migration fuer ein weiteres Schema: Revision-ID als
`<schema>_NNN` vergeben, nie bloss `NNN`. Bei jedem `alembic upgrade`-Aufruf (CLI, `make.ps1`,
Fixtures) immer `heads` (Plural) verwenden, nie `head`.
