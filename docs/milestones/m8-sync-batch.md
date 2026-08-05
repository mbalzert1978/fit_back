# M8 — Sync-Batch (Offline-Betrieb)

**Bezug BACKEND.md:** Abschnitt 7, Abschnitt 8.8.
**Voraussetzung:** M3, M4, M6, M7 (jede unterstützte Operation muss als Einzel-Endpunkt bereits
existieren — dieser Meilenstein baut nur die Batch-Hülle darum).

## Ziel

Ein Endpunkt, der alle im Client gesammelten Offline-Operationen in einem Rutsch entgegennimmt.

## Scope

`POST /api/v1/sync/batch` — verarbeitet `operations` in gesendeter Reihenfolge, eine
fehlgeschlagene Operation stoppt die Verarbeitung nicht, `opId` ist zugleich Idempotency-Key.

Unterstützte `type`-Werte (aus Abschnitt 7 — jeder muss zum Zeitpunkt dieses Tickets bereits als
Einzel-Use-Case existieren, dieser Meilenstein registriert sie nur im Batch-Dispatcher):
`diary.addEntry`, `diary.updateEntry`, `diary.moveEntry`, `diary.deleteEntry`,
`catalog.createProduct`, `recipes.createRecipe`, `recipes.updateRecipe`, `health.putActivity`.

## Architektur-Hinweis

Der Batch-Endpunkt ruft **dieselben** Application-Handler auf, die die Einzel-Endpunkte auch
nutzen (kein Duplikat der Fachlogik) — er ist eine reine Orchestrierungsschicht, die
`opId`→Idempotenz, Reihenfolge und Teilfehler-Aggregation übernimmt.

## Tests (Abschnitt 9)

- Reihenfolge-Test: Operationen werden strikt in Sende-Reihenfolge verarbeitet.
- Teilfehler-Test: eine fehlgeschlagene Operation stoppt nicht die folgenden; `problem`-Body pro
  `failed`-Eintrag ist valides RFC-7807.
- Idempotenz-Test: `opId` zweimal ⇒ `status: "duplicate"` beim zweiten Mal.
- Integrationstest je unterstütztem `type`-Wert (mind. ein `applied`-Fall), `curl`-Beispiel mit
  gemischtem Batch (ein `applied`, ein `duplicate`, ein `failed`).
