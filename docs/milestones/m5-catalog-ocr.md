# M5 — Catalog: Foto-Upload, OCR-Agent, Erfassung aus OCR

**Bezug BACKEND.md:** Abschnitt 2 (OCR-Teil), Abschnitt 8.5.
**Voraussetzung:** M3 (`Product`-Aggregate, `Origin.UserOcr`-Fall existiert bereits als Typ).

## Ziel

Der zweite Zweig des Kernversprechens: Barcode nicht gefunden → Foto der Nährwerttabelle → OCR →
Nutzer bestätigt → Produkt ist angelegt.

## Scope

Aggregate: `NutritionPhoto` (inkl. `OcrStatus`-Union `Uploaded/Processing/Completed/Failed`,
`OcrResult`-Value-Object mit `OcrField`-Union `Recognised/NotFound`, `Confidence` mit
`Level`-Union, `DetectedBasis`-Union).

Use Cases: `UploadNutritionPhoto`, `GetPhotoResult`, `CreateProductFromOcr`.

**OCR-Job-Verarbeitung** (technische Entscheidung, siehe `01-technical-decisions.md`):
Postgres-natives Queue-Pattern — Tabelle `catalog.ocr_jobs`, Worker via
`SELECT … FOR UPDATE SKIP LOCKED`, sofortige Zustellung über `LISTEN/NOTIFY` statt Polling. Timeout
30 s, zwei Wiederholungen, danach `Status = Failed`. `INutritionOcrAgent`-Port (`Protocol`) —
konkrete Vision-Modell-Implementierung austauschbar, für dieses Milestone genügt ein
Test-/Stub-Adapter plus die Port-Definition; die produktive Implementierung ist ein eigenes,
separat vergebbares Ticket (externe Abhängigkeit, kann parallel laufen).

**Blob-Speicher:** MinIO (lokal)/S3-kompatibel (Produktion) hinter `BlobStorage`-Port, siehe
`01-technical-decisions.md`.

API: `POST /api/v1/catalog/photos` (multipart), `GET /api/v1/catalog/photos/{photoId}`,
`POST /api/v1/catalog/products` jetzt zusätzlich mit befülltem `sourcePhotoId`-Pfad
(`Origin.UserOcr`).

## Tests (Abschnitt 9)

- Domain-Unit-Tests: `Confidence.Level`-Schwellen (0.90/0.70), `OcrField.NotFound` statt
  `null`-Wert, Timeout/Retry-Verhalten führt zu `Failed`.
- Value-Object-Tests (`Confidence`-Range 0-1, `BlobReference`).
- Tagged-Union-Serialisierungstests (`OcrStatus`, `OcrField`, `DetectedBasis`,
  `Confidence.Level`).
- Job-Queue-Test: zwei nebenläufige Worker beanspruchen nie denselben `ocr_jobs`-Datensatz
  (`SKIP LOCKED` funktioniert wie erwartet).
- Integrationstests je Endpunkt inkl. Fehlerfälle (`image-too-large`, `unsupported-media-type`,
  `photo-not-found`), Polling-Verhalten (`Processing` → `Completed`/`Failed`), `curl`-Beispiele
  gegen Docker Compose (inkl. MinIO).
