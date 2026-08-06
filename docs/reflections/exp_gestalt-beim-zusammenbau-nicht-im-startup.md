---
schema_version: 1
name: gestalt-beim-zusammenbau-nicht-im-startup
description: Was zur Gestalt der Anwendung gehoert (Middleware, Router, Handler) entsteht auf Modulebene; der Lifespan legt ausschliesslich Ressourcen an - `add_middleware` im Startup kommt bei Starlette immer zu spaet
type: project
frequency: 1
last_triggered: 2026-08-06
decay_eligible: true
---

Zwei Lebensdauern, die nicht vermischt werden: **Gestalt** (Middleware,
Exception-Handler, Router) steht auf Modulebene fest, **Ressourcen** (Engine,
Registrierungen, Worker) entstehen im Lifespan. Konkret bei Starlette/FastAPI:
`add_middleware` im Lifespan wirft immer `RuntimeError: Cannot add middleware
after an application has started` - die Middleware-Kette wird beim ersten
ASGI-Aufruf gebaut, und der erste ASGI-Aufruf **ist** der Lifespan-Aufruf.

**Why:** `src/main.py` rief im Lifespan `setup_idempotency_middleware(app)` auf,
um der Middleware den erst dort entstehenden DB-Pool mitzugeben. Ergebnis:
`lifespan.startup.failed`, keine einzige bediente Anfrage. Gemerkt hat es
niemand, weil der einzige Test das Modul nur *importierte*. Die Loesung ist
nicht, den Lifespan frueher laufen zu lassen, sondern die Abhaengigkeit
umzudrehen: die Middleware liest die Engine je Anfrage aus `app.state`, statt
sie im Konstruktor zu bekommen. Vollstaendig in
[`docs/decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md`](../decisions/2026-08-06-1500-ein-db-weg-und-die-middleware-die-nie-lief.md).

**How to apply:** Bei jedem Eingriff in den Einstiegspunkt fragen: *gehoert das
zur Gestalt oder ist es eine Ressource?* Braucht ein Gestalt-Baustein eine
Ressource, die es beim Zusammenbau noch nicht gibt, wird sie zur Laufzeit
gelesen (`app.state`), nicht die Registrierung verschoben. Ein Smoke-Test, der
den Lifespan **wirklich faehrt** - ueber das rohe ASGI-Protokoll, denn nur
dieser Aufruf baut die Middleware-Kette wie `uvicorn` -, faengt die ganze
Fehlerklasse; ein Import-Test tut es nicht. Verwandt:
[[first-live-execution-surfaces-latent-bugs]],
[[fixture-die-none-liefert-ist-ein-ausschalter]].
