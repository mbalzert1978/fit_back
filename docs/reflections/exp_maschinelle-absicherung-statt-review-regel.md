---
schema_version: 1
name: maschinelle-absicherung-statt-review-regel
description: Eine Architektur-Regel, die sich mechanisch pruefen laesst (Import-Richtung, Schichtung, Dateiablage), gehoert in einen Linter-Contract - nicht in ein LLM-Review; als blosse Prosa-Regel wird sie zuverlaessig verletzt und vom Gate durchgewunken
type: project
frequency: 2
last_triggered: 2026-08-06
decay_eligible: false
---

Jede Architektur-Regel zuerst darauf pruefen, ob sie **mechanisch entscheidbar** ist. Wenn ja,
gehoert sie in ein Werkzeug (import-linter-Contract, Pfad-Check-Skript), nicht in eine
Review-Checkliste. Ein LLM-Review ist fuer Urteilsfragen da, nicht fuer Fakten, die ein Parser
feststellen kann.

**Why:** `.rules/python/python-feature-slices.md` forderte seit Projektbeginn „`domain/` haengt nur
an der stdlib". Der `.importlinter`-Contract deckte aber nur die Context-Grenzen ab, nicht die
Domaenen-Reinheit. Ergebnis: `src/shared_kernel/` importierte real `starlette` (4x), `fastapi`
(3x), `pydantic` und `asyncpg`, verteilt ueber mehrere **bereits gemergte** Tickets — und das
QA-Gate hatte jedes Mal `APPROVE` gegeben. Nach Ergaenzung zweier Contracts (`domain-purity` gegen
externe Pakete, `context-layers` fuer `infrastructure -> application -> domain`) faellt derselbe
Verstoss in unter einer Sekunde auf, mit Datei und Zeilennummer, und kann kein Review mehr
passieren. Vgl. [exp_referenzimplementierung-schlaegt-prosa.md](exp_referenzimplementierung-schlaegt-prosa.md)
fuer die zweite Haelfte derselben Ursache.

**How to apply:** Beim Schaerfen eines Gates zuerst fragen: „Welcher Teil dieser Regel ist ein
Fakt, kein Urteil?" — Import-Kanten, Datei- und Ordnerablage, Vorhandensein geforderter Artefakte,
Namensmuster. Diesen Teil in `.importlinter`/ein Skript verlagern und **verifizieren, dass er einen
echten Verstoss auch faengt** (Probe-Datei mit bewusstem Verstoss anlegen, Contract laufen lassen,
Probe wieder entfernen) — ein gruener Contract, der nichts pruefen kann, ist schaedlicher als
keiner. `include_external_packages = True` ist noetig, damit import-linter externe Pakete
ueberhaupt als verbotene Ziele sieht.
