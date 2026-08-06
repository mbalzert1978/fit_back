# Neuschnitt des Shared Kernel nach dem ersten Slice

**Entschieden:** 2026-08-06, 13:30 — der in
[`2026-08-06-0751`](2026-08-06-0751-slice-form-test-api-baureihenfolge.md) auf „nach dem ersten
Slice" vertagte Schnitt.

## Der Maßstab

Der Shared Kernel hängt an **nichts außer der stdlib**. Alles andere hat einen anderen Ort:

| Braucht | Gehört nach |
|---|---|
| FastAPI, Pydantic (HTTP-Format) | `src/api/` |
| Starlette-Middleware, asyncpg, SQLAlchemy | `src/shared_infrastructure/` |
| nichts | `src/shared_kernel/` |

Das ist ab sofort keine Prosa mehr: `src.shared_kernel` steht im `domain-purity`-Contract in
`setup.cfg`. Ein Rückfall bricht die CI, statt beim nächsten Review aufzufallen oder nicht.

## Verschoben

- `main.py` → `src/main.py`. Der Einstiegspunkt lag als einziges Modul im Repo-Root; bemängelt
  schon in [`2026-08-06-0702`](2026-08-06-0702-qa-gate-haerten-struktur-review.md). Start jetzt
  über `python -m src.main` (Dockerfile, `make.ps1 run`, README nachgezogen).
- `problem_details.py`, `exception_handlers.py` → `src/api/` — beide sind HTTP-Format, nicht
  Domänen-Vokabular.
- `idempotency.py` → `src/shared_infrastructure/` — ASGI-Middleware über einer Tabelle.
- `src/shared_kernel/tests/` → `tests/api/` bzw. `tests/shared_infrastructure/`, den Modulen
  hinterher. Ein `tests/`-Ordner **innerhalb** von `src/` war ohnehin die Ausnahme: Specs liegen
  im Slice (`specs/`), Integrationstests unter `tests/`.

## Entfernt

Beides hatte **keinen einzigen Produktions-Aufrufer** — benutzt wurde es ausschließlich von den
eigenen Tests:

- **`exceptions.py` (`DomainException`) samt `domain_exception_handler`.** Ein zweiter,
  Exception-basierter Fehlerkanal neben der Response-Union der Slices. Fachliche Fehlausgänge
  tragen die Slices in ihrer Union, und der Router wählt daraus Statuscode und Body — sichtbar an
  einem vollständigen `match`. Ein geworfener Fehler daneben wäre genau die Verzweigung, die man
  beim Lesen nicht mehr sieht. Der `RequestValidationError`-Handler bleibt: den wirft FastAPI
  selbst.
- **`concurrency.py` (`RowVersion`, `ConcurrencyConflictError`) samt `test_repositories.py`.**
  Optimistische Nebenläufigkeit über `If-Match` ist in `docs/Draft/BACKEND.md` Abschnitt 0
  vorgesehen und kommt mit Ticket 0015/0024 — aber nicht in dieser Form: ein
  `ConcurrencyConflictError(DomainException)` ist wieder Kontrollfluss über Exceptions, während
  ein Versionskonflikt ein Fall des `DomainError` seines Context ist. Die 400 Zeilen Test dazu
  prüften ein Dummy-Aggregat, das es nirgends gibt, gegen ein Fake-Repository — also den Fake.

Wiederherstellbar aus `f709514^`. Wird `If-Match` gebraucht, entsteht es neu in der Form, die der
Rest des Codes inzwischen hat.

## Was das ausschließt

Der Satz „das kommt in den Shared Kernel" ist ab jetzt an eine prüfbare Bedingung geknüpft: es
muss ohne jede externe Abhängigkeit auskommen **und** einen zweiten Nutzer haben (siehe
[`exp_kein-vorauseilendes-shared`](../reflections/exp_kein-vorauseilendes-shared.md)). Erfüllt
etwas nur die erste Hälfte, bleibt es, wo es entstanden ist.
