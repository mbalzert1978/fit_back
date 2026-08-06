---
schema_version: 1
name: first-live-execution-surfaces-latent-bugs
description: Wenn ein Ticket als erstes eine bislang nur "auf dem Papier" existierende Infrastruktur (Migrationen, Multi-Schema-Setup) wirklich gegen eine Live-Ressource ausfuehrt, ist eine Kaskade zuvor unentdeckter Bugs zu erwarten
type: project
frequency: 2
last_triggered: 2026-08-06
decay_eligible: false
---

Tooling-only Tickets ohne echten Ausfuehrungstest (z. B. Ticket 0003s Alembic-Grundgeruest, das
selbst keine Tests hatte) koennen ueber mehrere Folge-Tickets latente Bugs anhaeufen, die erst
sichtbar werden, wenn ein spaeteres Ticket die Infrastruktur zum ersten Mal wirklich gegen eine
Live-Ressource ausfuehrt.

**Why:** Ticket 0009 (pytest + testcontainers-postgres) war der allererste echte Migrationslauf
in diesem Repo und deckte in einer einzigen PR nacheinander fuenf voneinander unabhaengige,
zuvor latente Bugs auf: Postgres-Image-Version abweichend von docker-compose, Env-Var-Name-
Mismatch, sync statt async Alembic-Engine (nur asyncpg installiert), global nicht eindeutige
Revision-IDs ueber alle 7 Schema-Branches (siehe `exp_alembic-multi-schema-pitfalls`), und
DB-Schema-Namen abweichend von den in CLAUDE.md dokumentierten Context-Namen - Letzteres betraf
sogar bereits gemergten Code aus Ticket 0006.
**How to apply:** Bei einem Ticket, das explizit "zum ersten Mal echt ausfuehren" ist (erster
Docker-Start, erste Live-Migration, erster End-to-End-Testlauf einer zuvor nur tooling-only
existierenden Komponente), zusaetzliche Debugging-Runden einplanen statt nach dem ersten Fund
Gruenlicht zu erwarten - jeder behobene Fehler kann einen weiteren, unabhaengigen freilegen.
