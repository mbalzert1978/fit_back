---
id: "0007"
title: M0: Shared Kernel - IUserOwned-Mixin + UUIDv7-Helper + RowVersion/If-Match
status: blocked
milestone: M0
type: AFK
---

# M0: Shared Kernel - IUserOwned-Mixin + UUIDv7-Helper + RowVersion/If-Match

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

IUserOwned-Protocol/Mixin, das jede Repository-Query zwingend auf UserId filtert (Abschnitt 0.5), ein UUIDv7-Helper (zeitsortierte Ids, vom Client selbst erzeugt, Abschnitt 0.19-Kontext) sowie eine RowVersion/Optimistic-Concurrency-Basis (xmin-Mapping, If-Match-Header-Auswertung, 409 mit type=.../concurrency-conflict, Abschnitt 0.13).

## Acceptance criteria

- [ ] Ein Test-Repository, das IUserOwned nutzt, liefert nachweislich nur Zeilen des anfragenden UserId
- [ ] uuid7() liefert zeitsortierte, gueltige UUIDs (Unit-Test auf Monotonie)
- [ ] Ein Update ohne oder mit veraltetem If-Match liefert 409 mit type=.../concurrency-conflict und aktuellem Serverstand im Body (Mechanismus-Test mit Dummy-Aggregate)

## Blocked by

- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)
