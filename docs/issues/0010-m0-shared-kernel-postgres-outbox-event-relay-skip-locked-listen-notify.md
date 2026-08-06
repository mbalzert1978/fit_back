---
id: "0010"
title: M0: Shared Kernel - Postgres-Outbox + Event-Relay (SKIP LOCKED / LISTEN NOTIFY)
status: closed
milestone: M0
type: AFK
---

# M0: Shared Kernel - Postgres-Outbox + Event-Relay (SKIP LOCKED / LISTEN NOTIFY)

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

shared.outbox-Tabelle plus Relay-Worker fuer asynchrone Integration Events zwischen Bounded Contexts (siehe 'Cross-Context-Kommunikation' in 01-technical-decisions.md): Events werden transaktional mit dem Aggregate-Write geschrieben, der Relay-Worker holt sie per SELECT ... FOR UPDATE SKIP LOCKED ab und benachrichtigt Konsumenten per LISTEN/NOTIFY statt Polling. Kein Redis/Broker.

## Stand: Neubau, PR #10 geschlossen

Ein erster Anlauf (Branch `0010`, PR #10) wurde **geschlossen, nicht gemergt**. Kerndefekt:
`src/shared_kernel/outbox/` importierte `OutboxEvent` — ein SQLAlchemy-ORM-Modell — aus
`shared_infrastructure` und baute im `shared_kernel` selbst eine SQLAlchemy-Engine auf. Damit zeigte
die innerste, dependency-freie Schicht auf Infrastruktur; reparieren haette Neuschreiben bedeutet.
Der Branch bleibt erhalten — das `SELECT ... FOR UPDATE SKIP LOCKED`- und `LISTEN/NOTIFY`-SQL ist
fachlich brauchbar und als Vorlage verwendbar.

**Platzierung beim Neubau:** Der Outbox-Mechanismus ist Infrastruktur und gehoert vollstaendig nach
`src/shared_infrastructure/outbox/` — ORM-Modell, Relay, Worker, Publisher. In den `shared_kernel`
wandert davon nur, was dependency-frei ist und von mehreren Contexts gebraucht wird; das wird
gemaess [`2026-08-06-0751`](../decisions/2026-08-06-0751-slice-form-test-api-baureihenfolge.md)
**nach** dem ersten Slice entschieden, nicht vorab. Der `domain-purity`-Contract in `setup.cfg`
faengt einen Rueckfall maschinell ab.

**Einplanung:** direkt nach Stufe 1 von [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md).
Die Outbox blockiert ausschliesslich **Stufe 2** von 0011/0018/0026 sowie 0031 — kein Ticket
braucht sie fuer seine Stufe 1.

## Acceptance criteria

Flach, ohne Stufengliederung: reine Queue-Infrastruktur ohne eigene Fachregel (analog
[0031](0031-m5-ocr-job-queue-postgres-skip-locked-listen-notify-ocragent-port-stub-adapter.md)),
siehe [`00-overview.md`](../milestones/00-overview.md), „Ticket-Schnitt".

- [x] Ein Event, das transaktional mit einem Dummy-Aggregate-Write in die Outbox geschrieben wird, wird vom Relay-Worker zuverlaessig genau einmal an einen Test-Consumer zugestellt
- [x] Zwei nebenlaeufige Relay-Worker-Instanzen verarbeiten nie denselben Outbox-Eintrag doppelt (SKIP LOCKED greift nachweislich)
- [x] Zustellung erfolgt nahezu sofort (LISTEN/NOTIFY), nicht erst nach einem Polling-Intervall

## Blocked by

- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)

## Abschluss (2026-08-06)

Neu gebaut innerhalb von Ticket [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
und mit PR #11 gemergt (Squash `6d50b4e`); der erste Anlauf als PR #10 blieb geschlossen.

Der Mechanismus liegt vollstaendig in `src/infrastructure/outbox/` — Tabelle, Relay mit
`SELECT ... FOR UPDATE SKIP LOCKED`, transaktionales `pg_notify`, LISTEN-Worker — und
deklariert bewusst **keine Naht**: je Slice-Naht erfuellt eine duenne Klasse unter
`publishers/`. Die Outbox ist reiner Mechanismus, nicht die Schnittstelle.

Alle drei Akzeptanzkriterien sind in `tests/infrastructure/test_outbox.py` belegt:

| Kriterium | Test |
|---|---|
| genau einmalige Zustellung eines transaktional geschriebenen Events | `test_committetes_event_wird_genau_einmal_zugestellt` |
| keine Doppelverarbeitung durch nebenlaeufige Relays (SKIP LOCKED) | `test_nebenlaeufige_relays_verarbeiten_kein_event_doppelt` |
| Zustellung ohne Polling-Intervall (LISTEN/NOTIFY) | `test_worker_stellt_ohne_polling_intervall_zu` |

Gegenueber dem geschlossenen PR #10 umgedreht: kein ORM-Modell und nichts im
`shared_kernel`, NOTIFY weckt statt zuzustellen, bigint-Unix-Sekunden statt `timestamptz`,
Backoff als `next_attempt_at` statt `asyncio.sleep` unter Row-Locks, `failed_at` getrennt
von `processed_at`.

Siehe [`2026-08-06-1120-outbox-mechanismus-statt-naht.md`](../decisions/2026-08-06-1120-outbox-mechanismus-statt-naht.md).
