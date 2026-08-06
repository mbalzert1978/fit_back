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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/catalog/domain/`: OcrField, OcrResult, DetectedBasis, Confidence als geschlossene Tagged Unions; Confidence.Level mit Schwellen-Invarianten (Certain>=0.90, Review 0.70-0.89, Uncertain<0.70); OcrField.NotFound statt null; **nur stdlib**
- [ ] Domain-Error als Tagged Union (PhotoNotFound); Domain-Ports
- [ ] `contexts/catalog/application/get_photo_result/`: Command (photoId), Handler (orchestriert nur), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: Protocol fuer Photo-Ladevorgang; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/get_photo_result/test_api.py` + `application/get_photo_result/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/catalog/specs/get_photo_result/`: Photo mit Status Processing wird gepollt, Status Completed mit OcrResult, Status Failed mit FailureReason
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, laedt NutritionPhoto
- [ ] Integrationstest gegen Testcontainers-Postgres: Photos mit verschiedenen OcrStatus-Werten werden korrekt geladen
- [ ] Tagged-Union-Serialisierungstests (OcrField, DetectedBasis, Confidence.Level)

### Stufe 3 — HTTP

- [ ] `GET /api/v1/catalog/photos/{photoId}` liefert Response-Schema je OcrStatus (Processing/Completed/Failed) exakt wie im Draft (Abschnitt 2)
- [ ] 404 `photo-not-found`
- [ ] Confidence.Level-Schwellen in Responses korrekt (Domain-Unit-Test der Schwellen)
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel

## Blocked by

- Blocked by [0032](0032-m5-nutritionphoto-aggregate-uploadnutritionphoto-minio-adapter.md)
