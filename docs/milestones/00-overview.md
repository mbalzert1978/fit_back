# Meilensteine — Nährwert-Tracking-Backend

Abgeleitet aus [`docs/Draft/BACKEND.md`](../Draft/BACKEND.md), Abschnitt 8 „Reihenfolge der
Umsetzung", ergänzt um einen vorgezogenen Meilenstein 0 für das cross-cuttende Projekt-
Grundgerüst (ohne den Fehlerformat/Auth-Anteil aus Meilenstein 1 vorwegzunehmen, aber mit allem,
was *jeder* spätere Meilenstein technisch voraussetzt: Repo-Struktur, Docker-Compose, DB-Basis,
Shared Kernel).

Die fachliche Reihenfolge aus Abschnitt 8 bleibt unverändert; M0 ist rein technisch und liegt
davor, weil ohne ihn kein Context lauffähig wird.

## Technischer Rahmen dieser Portierung

Der Draft spezifiziert ASP.NET Core/C#. Dieses Repository ist ein Python-3.14-Projekt
(`pyproject.toml`, `.rules/python`); die fachlichen Regeln aus dem Draft werden 1:1 übernommen,
die technische Umsetzung erfolgt idiomatisch in Python nach `.rules/python/*`. Die dabei
getroffenen technischen Entscheidungen (Stack, Infrastruktur, Repo-Layout) stehen in
[`01-technical-decisions.md`](./01-technical-decisions.md) — dorthin verweisen alle Meilensteine
für Details, statt sie zu wiederholen.

## Meilenstein-Liste

| # | Titel | Bezug BACKEND.md | Voraussetzung |
|---|---|---|---|
| [M0](./m0-projekt-grundgeruest.md) | Projekt-Grundgerüst & Shared Kernel | Abschnitt 0 (Querschnitts-Regeln) | — |
| [M1](./m1-identity.md) | Identity & Access + Fehlerformat + Auth-Pipeline | Abschnitt 1, 8.1 | M0 |
| [M2](./m2-goals.md) | Goals & Preferences (Default-Profil) | Abschnitt 5, 8.2 | M1 |
| [M3](./m3-catalog-produkte.md) | Catalog: Produkt-Aggregat, Barcode-/Textsuche, manuelles Anlegen | Abschnitt 2 (ohne OCR), 8.3 | M1 |
| [M4](./m4-diary.md) | Diary: Slots, Tag, Einträge, Tagesaggregation | Abschnitt 3, 8.4 | M1, M2, M3 |
| [M5](./m5-catalog-ocr.md) | Catalog: Foto-Upload, OCR-Agent, Erfassung aus OCR | Abschnitt 2 (OCR-Teil), 8.5 | M3 |
| [M6](./m6-recipes.md) | Recipes | Abschnitt 4, 8.6 | M3, M4 |
| [M7](./m7-healthsync.md) | HealthSync | Abschnitt 6, 8.7 | M1, M4 |
| [M8](./m8-sync-batch.md) | Sync-Batch (Offline-Betrieb) | Abschnitt 7, 8.8 | M3, M4, M6, M7 |

## Querschnitts-Regeln (Abschnitt 0)

Die 13 Querschnitts-Regeln aus Abschnitt 0 des Drafts gelten **für jeden Meilenstein**, nicht nur
für M0. M0 baut die technischen Bausteine dafür (Idempotenz-Tabelle, Fehlerformat-Middleware,
`TimeProvider`-Äquivalent, Value-Object-Basis, Tagged-Union-Basis, Optimistic-Concurrency-Spalte);
jeder folgende Meilenstein wendet sie auf seine eigenen Aggregate an — das ist in jedem
Meilenstein-Dokument unter „Cross-Cutting-Check" explizit aufgeführt, damit es nicht stillschweigend
vergessen wird.

## Ticket-Schnitt: von der Domäne nach außen, Infrastruktur zuletzt

Verbindlich seit
[`2026-08-06-0751-slice-form-test-api-baureihenfolge.md`](../decisions/2026-08-06-0751-slice-form-test-api-baureihenfolge.md).
Ein Ticket bleibt ein **Tracer Bullet** — durchgehend von der Domäne bis nach außen — aber seine
Akzeptanzkriterien sind **in drei geordnete Stufen gegliedert**, und die Pipeline gibt Stufe 1
frei, bevor Stufe 2 beginnt:

| Stufe | Was entsteht | Fertig, wenn |
|-------|--------------|--------------|
| **1 — Slice** | `domain/` (VOs, Entitäten, Aggregatwurzel, Ports, Regeln), `application/<use_case>/` (Command, Handler, beide Mapper, Validatoren, Port-Adapter, public Naht), `test_api.py` + `fakes/`, Verhaltens-Specs | Die Specs sind **grün ohne jede Infrastruktur** — keine Datenbank, kein HTTP, kein Container. Ab hier ist das Verhalten des Use Case vollständig spezifiziert. |
| **2 — Infrastruktur** | Naht-Implementierung (SQLAlchemy-Repository, externer Adapter), Alembic-Migration, Outbox-Publikation, Integrationstest gegen Testcontainers | Der Slice läuft gegen echte Persistenz, Verhalten unverändert. |
| **3 — HTTP** | `src/api/<context>/`-Router, ProblemDetails-Mapping, Idempotency-Header, curl-Beispiel, End-to-End-Test | Der Endpunkt ist erreichbar und liefert das spezifizierte Verhalten. |

**Warum gestuft statt gebündelt:** In M0 bündelte jedes Ticket alle Stufen ununterscheidbar. Ein
Agent hat dann keinen Grund, mit der Domäne zu beginnen — er baut, was am sichtbarsten ist
(Endpunkt, ORM-Modell) und leitet die Domäne daraus ab. Genau so entstand die invertierte
Abhängigkeitsrichtung, die sich durch alle M0-PRs zieht. Die Stufung macht „Domäne zuerst"
**überprüfbar** statt nur empfohlen.

**Nur die Stufen, die es wirklich gibt.** Ein Use Case ohne HTTP-Oberfläche — ein Hintergrundjob,
ein Outbox-Consumer — hat **Stufe 1 und 2, aber keine Stufe 3**. Er bleibt ein vollwertiger Slice:
seine Fachlogik gehört in die Domäne, sein Verhalten wird über die Test-API spezifiziert, und der
Job-Scheduler ist Infrastruktur (Stufe 2), nicht die Fachlogik selbst. Nicht zu verwechseln mit dem
Fall darunter.

**Was ein Ticket nicht sein darf:** ein Ticket, das **nur** Stufe 2 oder **nur** Stufe 3 liefert,
ohne dass Stufe 1 in einem anderen Ticket bereits abgeschlossen ist. Das ist ein horizontaler
Schnitt, kein Tracer Bullet. Legitime Ausnahme: **rein technische** Arbeit ohne jeden eigenen Use
Case (Repo-Grundgerüst, Migrations-Baseline, ein reiner Aufräum-Job ohne Fachregel) — diese Tickets
tragen keine Domäne, behalten flache Kriterien und sind als solche erkennbar. Die Abgrenzung: Steckt
in der Aufgabe eine **Fachregel**, die man falsch implementieren könnte? Dann ist es ein Use Case
mit Stufe 1, egal ob ihn jemals ein HTTP-Request auslöst.

**Ein Ticket ist eine Liefereinheit, ein Use Case eine Code-Struktur — das ist nicht dasselbe.**
Ein Ticket darf mehrere Use Cases liefern, und tut es regelmäßig: „GetGoals + UpdateGoals" ist
**ein** Ticket mit **zwei** Use-Case-Ordnern (`application/get_goals/` und
`application/update_goals/`), jeder mit eigenem Command, eigenem Handler, eigenen beiden Mappern,
**eigener `test_api.py` und eigenen `fakes/`**. Sie teilen sich die Domäne des Contexts und den
`DomainError`, sonst nichts.

Was es **nie** gibt, ist ein zusammengelegter Use Case wie `get_and_update_goals`. Eine Abfrage und
ein Kommando sind zwei Operationen, und `python-feature-slices.md` ist da eindeutig: „Eine
Operation, die zwei Fragen in einem Flag beantwortet, ist zwei Operationen — trenne sie in zwei
Slices, nicht ein Flag im Handler", und „kein Mapper bedient mehrere Operationen". Ein Ticket-Titel
mit `+` oder `/` (`GetMe + UpdateProfile`, `UpdateEntryAmount / MoveEntry / DeleteEntry`) ist das
sichtbare Signal: so viele Operationen im Titel, so viele Use-Case-Ordner in Stufe 1.

**Abhängigkeiten gelten je Stufe, nicht je Ticket.** Ein `Blocked by`-Eintrag trägt deshalb einen
Stufen-Qualifier, wenn er nur einen Teil des Tickets betrifft:

```
- Blocked by [0010](…) — **nur Stufe 2**; Stufe 1 ist davon unabhaengig
```

Das ist kein Detail: Stufe 1 hat per Definition **keine** Infrastruktur, also kann sie auch nicht
von einem Infrastruktur-Ticket blockiert sein. Ohne den Qualifier bleibt ein Ticket unnötig als
`blocked` stehen, obwohl sein wertvollster Teil — die Domäne — sofort baubar wäre. Ein Ticket gilt
als `blocked` nur, wenn **Stufe 1** blockiert ist; ist bloß Stufe 2 oder 3 blockiert, ist es `open`.

**Aufteilen in mehrere Tickets** nur, wenn eine einzelne Stufe für sich genommen groß ist (z. B.
ein OCR-Adapter mit eigener Queue). Der Regelfall ist **ein Ticket je Feature mit drei gestuften
Kriterienblöcken** — das hält die Ticket-Zahl beherrschbar und die Verticality erhalten.

## Tests (Abschnitt 9)

Jeder Meilenstein liefert die in Abschnitt 9 geforderten Testarten für die von ihm eingeführten
Aggregate/Value Objects/Unions/Endpunkte mit (Domain-Unit-Tests, Value-Object-Tests,
Architekturtests, Union-Serialisierungstests, Rundungstests wo zutreffend, Idempotenz-Tests,
Integrationstests). Kein Meilenstein gilt als abgeschlossen, ohne dass diese Tests für seinen
Scope existieren und grün sind. Für die Kommunikation zwischen Bounded Contexts gilt zusätzlich
eine eigene Contract-Test-Ebene, siehe [`02-test-pyramide.md`](./02-test-pyramide.md).
