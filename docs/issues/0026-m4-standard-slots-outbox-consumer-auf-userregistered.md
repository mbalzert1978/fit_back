---
id: "0026"
title: M4: Standard-Slots-Outbox-Consumer auf UserRegistered
status: blocked
milestone: M4
type: AFK
---

# M4: Standard-Slots-Outbox-Consumer auf UserRegistered

## Parent

Meilenstein [M4](docs/milestones/m4-diary.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Outbox-Consumer, der auf UserRegistered (M1.1, ueber M0.10) reagiert und die drei Standard-Mahlzeiten-Slots anlegt: Fruehstueck, Mittagessen, Abendessen, in dieser Reihenfolge.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/diary/application/create_standard_slots_on_registration/`: Command (userId), Handler (orchestriert nur: laedt oder erzeugt User-Diary-Profil, legt genau drei MealSlots mit Namen Fruehstueck/Mittagessen/Abendessen in dieser Reihenfolge an), Request-Mapper und Response-Mapper
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Operation zum Laden/Anlegen des Nutzerprofils; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/create_standard_slots_on_registration/test_api.py` + `application/create_standard_slots_on_registration/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/diary/tests/create_standard_slots_on_registration/`: Slots werden in exakt dieser Reihenfolge angelegt, idempotent (doppelter Aufruf mit gleichem userId haelt Slots), andere Use Cases stoeren nicht
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] Outbox-Consumer-Job (M0.10), der auf `UserRegistered`-Events reagiert und den Handler aufruft
- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, ladet oder erzeugt User-Diary-Profil, persistiert die 3 Slots
- [ ] Integrationstest gegen Testcontainers-Postgres ueber die volle Kette (M1.1 → M0.10 → dieser Consumer → M4.1): Nach RegisterUser existiert genau ein DiaryDay-Profil mit genau drei Slots in Reihenfolge
- [ ] Contract-Test (siehe `docs/milestones/02-test-pyramide.md`, Form B): der Handler aus Stufe 1 wird gegen jedes kanonische UserRegistered-Beispiel aus `contexts/identity/contracts/events/user_registered/examples/` ausgefuehrt (kein Testcontainers-Setup noetig)

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
- Blocked by [0025](0025-m4-mealslot-aggregate-slot-crud-reorder.md)
- Blocked by [0010](0010-m0-shared-kernel-postgres-outbox-event-relay-skip-locked-listen-notify.md) — **nur Stufe 2**; Stufe 1 ist davon unabhaengig
