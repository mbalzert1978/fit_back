---
id: "0033"
title: M5: GetPhotoResult (Polling)
status: blocked
milestone: M5
type: AFK
---

# M5: GetPhotoResult (Polling)

## Parent

Meilenstein [M5](docs/milestones/m5-catalog-ocr.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/catalog/photos/{photoId} - Polling-Endpunkt, liefert je nach OcrStatus Processing/Completed(mit OcrResult inkl. Confidence-Level-Schwellen)/Failed(mit FailureReason).

## Acceptance criteria

- [ ] Response-Schema je Status exakt wie im Draft-Beispiel (Abschnitt 2)
- [ ] Confidence.Level: >=0.90 Certain, 0.70-0.89 Review, <0.70 Uncertain (Domain-Unit-Test der Schwellen)
- [ ] OcrField.NotFound statt eines null-Werts (kein value==null als Sonderfall im Code)
- [ ] 404 photo-not-found
- [ ] Tagged-Union-Serialisierungstests (OcrField, DetectedBasis, Confidence.Level), Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0032](0032-m5-nutritionphoto-aggregate-uploadnutritionphoto-minio-adapter.md)
