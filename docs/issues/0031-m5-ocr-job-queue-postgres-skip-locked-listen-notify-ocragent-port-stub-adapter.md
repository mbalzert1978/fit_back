---
id: "0031"
title: M5: OCR-Job-Queue (Postgres SKIP LOCKED/LISTEN NOTIFY) + OcrAgent-Port + Stub-Adapter
status: blocked
milestone: M5
type: AFK
---

# M5: OCR-Job-Queue (Postgres SKIP LOCKED/LISTEN NOTIFY) + OcrAgent-Port + Stub-Adapter

## Parent

Meilenstein [M5](docs/milestones/m5-catalog-ocr.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Tabelle catalog.ocr_jobs, Worker via SELECT ... FOR UPDATE SKIP LOCKED, sofortige Zustellung ueber LISTEN/NOTIFY. OcrAgent-Protocol-Port (extract(image) -> OcrResult), Timeout 30s, zwei Wiederholungen, danach Status=Failed. Fuer dieses Ticket genuegt ein Stub-Adapter (liefert deterministische Testwerte); die produktive Vision-Modell-Anbindung ist ein separates, spaeter vergebbares Ticket (siehe m5-catalog-ocr.md).

## Acceptance criteria

- [ ] Zwei nebenlaeufige Worker beanspruchen nie denselben ocr_jobs-Datensatz (SKIP LOCKED-Test)
- [ ] Ein Job, der laenger als 30s braucht bzw. zweimal fehlschlaegt, landet nachweislich auf Status=Failed
- [ ] OcrAgent-Port ist ein Protocol, der Stub-Adapter ist per DI austauschbar
- [ ] `./make.ps1 import-lint` gruen (Domaenen-Reinheit + Schichtung)

## Blocked by

- Blocked by [0010](0010-m0-shared-kernel-postgres-outbox-event-relay-skip-locked-listen-notify.md)
- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)
