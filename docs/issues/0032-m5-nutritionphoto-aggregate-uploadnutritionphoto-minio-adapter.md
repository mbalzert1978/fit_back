---
id: "0032"
title: M5: NutritionPhoto-Aggregate + UploadNutritionPhoto (MinIO-Adapter)
status: blocked
milestone: M5
type: AFK
---

# M5: NutritionPhoto-Aggregate + UploadNutritionPhoto (MinIO-Adapter)

## Parent

Meilenstein [M5](docs/milestones/m5-catalog-ocr.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

NutritionPhoto-Aggregate (OcrStatus-Union Uploaded/Processing/Completed/Failed, BlobReference), Use Case UploadNutritionPhoto, BlobStorage-Port mit MinIO-Adapter (S3-kompatibel).

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/catalog/domain/`: NutritionPhoto-Aggregatwurzel mit identitaetsbasierter Gleichheit; OcrStatus als geschlossene Tagged Union (Uploaded/Processing/Completed/Failed); BlobReference als Value Object; **nur stdlib**
- [ ] Domain-Error als Tagged Union (z. B. ImageTooLarge, UnsupportedMediaType); Domain-Ports als `Protocol`
- [ ] `contexts/catalog/application/upload_nutrition_photo/`: Command (photoId, imageBinary, mediaType), Handler (orchestriert nur), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: BlobStorage-Port mit **nur** den Operationen, die `upload_nutrition_photo` braucht; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/upload_nutrition_photo/test_api.py` + `application/upload_nutrition_photo/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/catalog/tests/upload_nutrition_photo/`: erfolgreicher Upload (Bild > 8MB wird abgelehnt, unsupported Media Type wird abgelehnt)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1; Alembic-Migration fuer `catalog.nutrition_photos`
- [ ] MinIO-Adapter implementiert BlobStorage-Port, speichert Bilder
- [ ] Integrationstest gegen Testcontainers-Postgres + MinIO-Container (aus docker-compose.yml)
- [ ] Tagged-Union-Serialisierungstest (OcrStatus)

### Stufe 3 — HTTP

- [ ] `POST /api/v1/catalog/photos` (multipart) liefert 202 mit photoId und status=Processing
- [ ] 413 `image-too-large` (>8MB), 415 `unsupported-media-type`
- [ ] Das hochgeladene Bild liegt danach nachweislich in MinIO (Integrationstest)
- [ ] Idempotency-Key-Header wird ueber die M0.6-Middleware ausgewertet
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel

## Blocked by

- Blocked by [0031](0031-m5-ocr-job-queue-postgres-skip-locked-listen-notify-ocragent-port-stub-adapter.md)
- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
