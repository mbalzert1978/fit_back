---
id: "0010"
title: M0: Shared Kernel - Postgres-Outbox + Event-Relay (SKIP LOCKED / LISTEN NOTIFY)
status: blocked
milestone: M0
type: AFK
---

# M0: Shared Kernel - Postgres-Outbox + Event-Relay (SKIP LOCKED / LISTEN NOTIFY)

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

shared.outbox-Tabelle plus Relay-Worker fuer asynchrone Integration Events zwischen Bounded Contexts (siehe 'Cross-Context-Kommunikation' in 01-technical-decisions.md): Events werden transaktional mit dem Aggregate-Write geschrieben, der Relay-Worker holt sie per SELECT ... FOR UPDATE SKIP LOCKED ab und benachrichtigt Konsumenten per LISTEN/NOTIFY statt Polling. Kein Redis/Broker.

## Acceptance criteria

- [ ] Ein Event, das transaktional mit einem Dummy-Aggregate-Write in die Outbox geschrieben wird, wird vom Relay-Worker zuverlaessig genau einmal an einen Test-Consumer zugestellt
- [ ] Zwei nebenlaeufige Relay-Worker-Instanzen verarbeiten nie denselben Outbox-Eintrag doppelt (SKIP LOCKED greift nachweislich)
- [ ] Zustellung erfolgt nahezu sofort (LISTEN/NOTIFY), nicht erst nach einem Polling-Intervall

## Blocked by

- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)
