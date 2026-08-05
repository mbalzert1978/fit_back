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

- [ ] POST /api/v1/catalog/photos (multipart) liefert 202 mit photoId und status=Processing
- [ ] 413 image-too-large (>8MB), 415 unsupported-media-type
- [ ] Das hochgeladene Bild liegt danach nachweislich in MinIO (Integrationstest gegen den Compose-Service)
- [ ] Tagged-Union-Serialisierungstest (OcrStatus), curl-Beispiel

## Blocked by

- Blocked by [0031](0031-m5-ocr-job-queue-postgres-skip-locked-listen-notify-ocragent-port-stub-adapter.md)
- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
