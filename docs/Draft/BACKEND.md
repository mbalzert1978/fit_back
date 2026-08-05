# Backend-Spezifikation — Nährwert-Tracking-App

Zielsystem: **ASP.NET Core 8 Web API, C#, DDD-Schnitt nach Bounded Contexts.**
Diese Datei ist die vollständige Vorgabe. Es gibt keine offenen Punkte, die vor Baubeginn geklärt werden müssen; wo Entscheidungen offen wären, sind sie hier bereits getroffen.

---

## 0. Rahmenbedingungen

**Produktidee.** Ernährungstagebuch mit dem Kernversprechen *schnelle Datenerfassung statt KI-Fotobewertung*. Ablauf: Barcode scannen → Produkt gefunden → Menge → Tagebuch. Wird der Barcode nicht gefunden, fotografiert der Nutzer die Nährwerttabelle; ein OCR-Agent extrahiert die Werte, der Nutzer bestätigt sie, und das Produkt ist damit in der Datenbank angelegt.

**Architektur.**

- Ein Deployment (modularer Monolith), ein Projekt pro Bounded Context:
  `Contexts/Identity`, `Contexts/Catalog`, `Contexts/Diary`, `Contexts/Recipes`, `Contexts/Goals`, `Contexts/HealthSync`.
- Pro Context je eine Schicht `Domain` / `Application` / `Infrastructure`; die Web-API ist ein gemeinsames Host-Projekt mit einem Controller-Ordner je Context.
- Kein Context greift auf die Tabellen eines anderen zu. Kommunikation über Application-Services oder Domain Events (In-Process, MediatR).
- Persistenz: PostgreSQL, EF Core, ein `DbSchema` je Context (`identity`, `catalog`, `diary`, `recipes`, `goals`, `health`).
- Alle Ids sind `Guid` (v7, zeitsortiert). Der Client erzeugt Ids für neu angelegte Objekte selbst (wichtig für Offline-Betrieb, siehe Idempotenz).

**Querschnitts-Regeln, die für ALLE Contexts gelten.**

1. **Nährwerte werden IMMER pro 100 g gespeichert**, als `decimal(8,2)`. Portionen und Mengen werden ausschließlich im Client oder in der Read-Projektion daraus gerechnet. Es wird nie ein bereits skalierter Wert persistiert.
2. **Rundung ist Präsentationslogik, nicht Domänenlogik.** Das Backend liefert ungerundete Dezimalwerte. Nur die Read-Endpunkte, die aggregierte Tageswerte liefern, runden nach der Nutzereinstellung (siehe Context *Goals*).
3. **Idempotenz.** Alle `POST`/`PUT`, die Objekte anlegen, akzeptieren den Header `Idempotency-Key` (Guid). Ein bereits verarbeiteter Key liefert die ursprüngliche Antwort mit `200` statt `201`. Speicherung in Tabelle `shared.idempotency_keys` (Key, UserId, RequestHash, ResponseBody, CreatedUtc), TTL 7 Tage.
4. **Zeit und Datum.** Ein Tagebuch-Tag ist ein `DateOnly` in der Zeitzone des Nutzers (`Identity.User.TimeZoneId`, IANA). Alle Zeitstempel im Transport sind UTC ISO-8601.
5. **Mandantentrennung.** Jede Anfrage trägt eine Nutzeridentität; jede Repository-Abfrage filtert zwingend auf `UserId`. EF Core Global Query Filter auf `IUserOwned`.
6. **Fehlerformat.** Immer RFC 7807 `application/problem+json`:
   ```json
   { "type": "https://api.example/errors/product-not-found",
     "title": "Produkt nicht gefunden",
     "status": 404,
     "detail": "Zu EAN 4008400401027 existiert kein Produkt.",
     "instance": "/api/v1/catalog/products/by-barcode/4008400401027",
     "errors": { "feldname": ["Meldung"] } }
   ```
   Validierungsfehler `400` mit gefülltem `errors`. Kein anderes Fehlerformat.
7. **Versionierung.** Alle Routen unter `/api/v1/`.
8. **Auth.** Bearer-JWT im Header `Authorization`. Access-Token 15 min, Refresh-Token 60 Tage (rotierend).
9. **Sprache.** Fehlermeldungen und serverseitige Texte über Resource-Files `de-DE` (Default) und `en-US`, gewählt über `Accept-Language`.
10. **Keine Primitives in Aggregaten (Primitive Obsession vermeiden).** Ein Aggregate oder eine Entity hält **niemals** `string`, `int`, `decimal` oder `Guid` direkt als fachliches Feld. Jedes fachliche Feld ist ein Value Object mit eigener Validierung im Konstruktor — ungültige Instanzen dürfen gar nicht erst entstehen. Muster für alle Value Objects:
    ```csharp
    public readonly record struct Grams
    {
        public decimal Value { get; }
        private Grams(decimal value) => Value = value;

        public static Grams From(decimal value) =>
            value is > 0 and <= 5000
                ? new Grams(value)
                : throw new DomainException(ErrorCodes.GramsOutOfRange);

        public static implicit operator decimal(Grams g) => g.Value;
    }
    ```
    Ids sind ebenfalls Value Objects (`UserId`, `ProductId`, `RecipeId`, `DiaryEntryId`, `MealSlotId`, `PhotoId`) — ein `ProductId` darf sich nicht versehentlich einer Methode zuweisen lassen, die eine `RecipeId` erwartet. EF Core bindet sie über `HasConversion` bzw. `ComplexProperty` an; die Konvertierungen liegen gesammelt in `Infrastructure/Persistence/ValueConverters`.

11. **Discriminated Unions statt Enums.** Es gibt in der Domäne **keine** `enum`. Jede Menge fachlicher Alternativen ist eine geschlossene Typhierarchie, damit Verhalten am Fall hängt statt an einem `switch`, und der Compiler Vollständigkeit erzwingt:
    ```csharp
    [JsonPolymorphic(TypeDiscriminatorPropertyName = "kind")]
    [JsonDerivedType(typeof(Physiological), "physiological")]
    [JsonDerivedType(typeof(Declaration),   "declaration")]
    public abstract record EnergyFactors
    {
        public abstract decimal Carbs { get; }
        public abstract decimal Protein { get; }
        public abstract decimal Fat { get; }

        public sealed record Physiological : EnergyFactors   // Atwater
        { public override decimal Carbs => 4.1m; public override decimal Protein => 4.1m; public override decimal Fat => 9.3m; }

        public sealed record Declaration : EnergyFactors     // VO (EU) 1169/2011
        { public override decimal Carbs => 4m;   public override decimal Protein => 4m;   public override decimal Fat => 9m; }
    }
    ```
    Auswertung ausschließlich über Pattern Matching mit vollständigen Zweigen (`switch` expression, kein `default`, das einen Fall verschluckt). Persistenz über einen Diskriminator-String; im JSON-Transport erscheint der Diskriminator als kleingeschriebener `kind`-Wert, wie in den Beispielen unten. Wo eine Union Nutzdaten trägt (z. B. `EntrySource`), trägt der jeweilige Fall genau die Felder, die er braucht — keine nullable Sammelfelder.

12. **`DateTimeOffset` statt `DateTime`.** Jeder Zeitstempel in Domäne, Persistenz und Transport ist `DateTimeOffset` (PostgreSQL `timestamptz`). `DateTime` kommt im gesamten Lösungspfad nicht vor — dafür eine Analyzer-Regel aktivieren. Die Zeitquelle ist `TimeProvider` (über DI injiziert), nie `DateTimeOffset.UtcNow` direkt im Code, damit Zeitverhalten testbar bleibt. Ausnahme sind reine Kalendertage: Der Tagebuch-Tag ist ein `DateOnly` in einem Value Object `DiaryDate` — ein Tag hat keine Uhrzeit und darf keine bekommen.

13. **Optimistic Concurrency.** Jedes Aggregate hat `RowVersion` (`uint`, PostgreSQL `xmin` gemappt). Schreiboperationen senden `If-Match: <RowVersion>`; Konflikt ⇒ `409` mit `type: .../concurrency-conflict` und dem aktuellen Serverstand im Body.

---

## 1. Bounded Context: Identity & Access

**Verantwortung.** Registrierung, Anmeldung, Sitzungen, Löschung des Kontos, Stammdaten des Nutzers, mit denen andere Contexts nicht arbeiten dürfen (E-Mail, Passwort-Hash).

### Aggregates

**`User` (Aggregate Root)**

| Feld | Typ | Regel |
|---|---|---|
| `Id` | `UserId` | |
| `Email` | `EmailAddress` | eindeutig, case-insensitive normalisiert |
| `PasswordHash` | `PasswordHash` | Argon2id, kapselt Algorithmus und Verifikation |
| `DisplayName` | `DisplayName` | 1–60 Zeichen |
| `TimeZone` | `UserTimeZone` | IANA-Id, gegen `TimeZoneInfo` geprüft, Default `Europe/Berlin` |
| `Locale` | `Locale` (Union: `German`, `English`) | Default `German` |
| `Status` | `AccountStatus` (Union: `Active`, `Suspended`, `PendingDeletion(DateTimeOffset EffectiveAt)`) | der Fall trägt sein Datum selbst |
| `CreatedAt` | `DateTimeOffset` | |

Invarianten: E-Mail eindeutig; ein `PendingDeletion`-Konto kann sich nicht mehr anmelden; `DisplayName` nicht leer.

**`RefreshToken` (eigenes Aggregate)** — `Id`, `UserId`, `TokenHash`, `ExpiresUtc`, `RevokedUtc?`, `ReplacedById?`. Rotation: Bei Verwendung wird der alte Token revoked und ein neuer ausgegeben. Wiederverwendung eines revoked Tokens ⇒ alle Tokens des Nutzers revoken (`401`).

### Use Cases

- `RegisterUser(email, password, displayName, locale, timeZoneId)` → legt `User` an, veröffentlicht `UserRegistered`. **Wichtig:** Der Context *Goals* legt auf dieses Event hin ein Default-Zielprofil an, der Context *Diary* die drei Standard-Mahlzeiten-Slots (Frühstück, Mittagessen, Abendessen, in dieser Reihenfolge).
- `Login(email, password)` → Access + Refresh Token.
- `RefreshSession(refreshToken)`.
- `Logout(refreshToken)`.
- `UpdateProfile(displayName?, locale?, timeZoneId?)`.
- `ChangePassword(current, new)` → revoked alle Refresh-Tokens.
- `RequestAccountDeletion()` → Status `PendingDeletion`, Löschung nach 30 Tagen per Hintergrundjob; veröffentlicht `UserDeletionRequested`, alle anderen Contexts löschen ihre Daten auf `UserDeleted`.

### API-Contracts

```
POST /api/v1/identity/register
Body  { "email": "a@b.de", "password": "…", "displayName": "Markus",
        "locale": "de", "timeZoneId": "Europe/Berlin" }
201   { "userId": "…", "accessToken": "…", "refreshToken": "…", "expiresInSeconds": 900 }
409   type=email-already-registered
400   Passwort < 10 Zeichen ⇒ errors.password
```

```
POST /api/v1/identity/login
Body  { "email": "…", "password": "…" }
200   { "userId", "accessToken", "refreshToken", "expiresInSeconds" }
401   type=invalid-credentials   (gleiche Antwort bei unbekannter E-Mail — keine User-Enumeration)
403   type=account-pending-deletion
```

```
POST /api/v1/identity/refresh        Body { "refreshToken" } → 200 wie login | 401
POST /api/v1/identity/logout         Body { "refreshToken" } → 204
GET  /api/v1/identity/me             → 200 { userId, email, displayName, locale, timeZoneId, createdUtc }
PATCH /api/v1/identity/me            Body { displayName?, locale?, timeZoneId? } → 200 (wie GET)
POST /api/v1/identity/me/password    Body { currentPassword, newPassword } → 204 | 400 | 401
DELETE /api/v1/identity/me           → 202 { "deletionEffectiveUtc": "…" }
```

---

## 2. Bounded Context: Catalog (Produkte & OCR-Erfassung)

**Verantwortung.** Produktstammdaten mit Nährwerten pro 100 g, Barcode-Suche, Textsuche, die Erfassung neuer Produkte über Foto + OCR. Dieser Context trägt das Kernversprechen der App.

### Aggregates

**`Product` (Aggregate Root)**

| Feld | Typ | Regel |
|---|---|---|
| `Id` | `ProductId` | |
| `Barcode` | `Ean?` | 8/12/13/14 Stellen, Prüfziffer im Konstruktor validiert; null erlaubt (manuell angelegte Produkte) |
| `Name` | `ProductName` | 1–120 Zeichen, Pflicht |
| `Brand` | `BrandName?` | 0–80 |
| `Nutrients` | `NutrientsPer100` | siehe unten |
| `BasisUnit` | `BasisUnit` (Union: `Gram`, `Milliliter`) | Default `Gram` |
| `Origin` | `ProductOrigin` (Union: `UserOcr(PhotoId)`, `UserManual`, `Curated`, `External(SourceName)`) | ersetzt die früheren Felder `Source` **und** `SourcePhotoId` — die Foto-Id gehört nur zum OCR-Fall |
| `Visibility` | `ProductVisibility` (Union: `Private(UserId Owner)`, `Public`) | aus `UserOcr`/`UserManual` erzeugte Produkte starten `Private`; der Besitzer hängt am Fall, nicht als nullable Feld daneben |
| `VerifiedByUser` | `bool` | einziges echtes Primitive: ein Ja/Nein ohne weitere Fachlichkeit |
| `CreatedAt`, `UpdatedAt` | `DateTimeOffset` | |
| `RowVersion` | `uint` | technisch, nicht fachlich |

**Value Object `NutrientsPer100`** — die Felder sind ihrerseits Value Objects, keine nackten Dezimalzahlen:
`Kcal` (`Energy`), `Fat` (`NutrientAmount`), `SaturatedFat` (`NutrientAmount?`), `Carbs` (`NutrientAmount`), `Sugar` (`NutrientAmount?`), `Protein` (`NutrientAmount`), `Salt` (`NutrientAmount?`).
`NutrientAmount` erzwingt ≥ 0 und ≤ 100 pro 100 g, `Energy` erzwingt ≥ 0 und ≤ 900 kcal. Die übergreifenden Regeln (`SaturatedFat ≤ Fat` usw.) prüft `NutrientsPer100` beim Erzeugen — nicht der aufrufende Service.

Invarianten:
- `Kcal`, `Fat`, `Carbs`, `Protein` sind **Pflicht** (nicht null), damit ein Produkt gespeichert werden darf. `SaturatedFat`, `Sugar`, `Salt` dürfen null bleiben — die App zeigt sie dann als „Wert fehlt".
- Alle Werte ≥ 0; `SaturatedFat ≤ Fat`; `Sugar ≤ Carbs`; `Fat + Carbs + Protein ≤ 100` (bei Basis 100 g).
- Ein `Barcode` ist innerhalb `Visibility = Public` eindeutig. Private Produkte dürfen denselben Barcode tragen (der Nutzer hat sein eigenes erfasst).

**`NutritionPhoto` (Aggregate Root)** — die fotografierte Nährwerttabelle und das OCR-Ergebnis.

| Feld | Typ |
|---|---|
| `Id` | `PhotoId` |
| `UserId` | `UserId` |
| `Barcode` | `Ean?` |
| `Blob` | `BlobReference` (Objektspeicher, nicht in der DB) |
| `Status` | `OcrStatus` — Union: `Uploaded`, `Processing`, `Completed(OcrResult Result)`, `Failed(FailureReason Reason)` |
| `CreatedAt` | `DateTimeOffset` |

Die Union macht die früheren nullable Felder überflüssig: Ein Ergebnis existiert genau im Fall `Completed`, ein Fehlergrund genau im Fall `Failed`, ein Abschlusszeitpunkt gehört zu beiden Endzuständen und wird dort geführt.

**Value Object `OcrResult`** — je Nährwert ein `OcrField`, plus `DetectedBasis` und `DetectedProductName?`.
- `OcrField` ist selbst eine Union: `Recognised(NutrientAmount Value, Confidence Confidence, RawText Raw)` oder `NotFound`. Damit gibt es kein `Value == null` mehr, das an jeder Auswertungsstelle geprüft werden müsste.
- `Confidence` ist ein Value Object über 0–1 mit der Einstufung als Verhalten am Typ: `Level` liefert `Certain` (≥ 0,90), `Review` (0,70–0,89) oder `Uncertain` (< 0,70) — ebenfalls als Union. Die Schwellen stehen genau hier, nicht im Client.
- `DetectedBasis` ist eine Union: `Per100g`, `Per100ml`, `PerPortion(Grams PortionSize)`, `Unknown`.

Regel für die Confidence-Darstellung im Client (hier fixiert, damit beide Seiten identisch entscheiden):
`≥ 0.90` = sicher · `0.70–0.89` = prüfen · `< 0.70` = unsicher · `Value == null` = fehlt.

### Use Cases

- `FindProductByBarcode(ean)` — sucht zuerst in eigenen privaten Produkten des Nutzers, dann in `Public`. Kein Treffer ⇒ `404` (das ist der Auslöser für den Foto-Flow, kein Fehler im Sinne von „kaputt").
- `SearchProducts(query, take, skip)` — Volltext über `Name` und `Brand` (PostgreSQL `tsvector`, deutsch), eigene Produkte zuerst.
- `UploadNutritionPhoto(barcode?, image)` — legt `NutritionPhoto` an, stößt asynchron den OCR-Agenten an, liefert sofort die `photoId` zurück.
- `GetPhotoResult(photoId)` — Polling-Endpunkt für den Client.
- `CreateProductFromOcr(photoId, name, brand?, barcode?, nutrients)` — der Nutzer hat die Werte bestätigt oder korrigiert; legt `Product` mit `Source = UserOcr`, `VerifiedByUser = true` an.
- `CreateProductManually(name, brand?, barcode?, nutrients)`.
- `UpdateProduct(productId, …)` — nur durch den Besitzer eines privaten Produkts.

**OCR-Agent.** Läuft serverseitig (Hosted Service + Queue), nicht auf dem Gerät. Vertrag der Anbindung: `INutritionOcrAgent.ExtractAsync(Stream image, CancellationToken) → OcrResult`. Die konkrete Implementierung (Vision-Modell) ist austauschbar; die Domäne kennt nur dieses Interface. Timeout 30 s, zwei Wiederholungen, danach `Status = Failed`.

### API-Contracts

```
GET /api/v1/catalog/products/by-barcode/{ean}
200 { "id","barcode","name","brand","basisUnit":"Gram","source":"Curated",
      "verifiedByUser":true,
      "nutrientsPer100": { "kcal":184,"fat":9.2,"saturatedFat":5.8,
                           "carbs":3.1,"sugar":2.9,"protein":21.0,"salt":null } }
404 type=product-not-found       ← Client startet daraufhin den Foto-Flow
400 type=invalid-barcode         ← Prüfziffer falsch
```

```
GET /api/v1/catalog/products?query=skyr&take=20&skip=0
200 { "items":[ { …Produkt… } ], "total": 37 }
```

```
POST /api/v1/catalog/photos            (multipart/form-data)
Felder: file (image/jpeg, max 8 MB), barcode (optional)
202 { "photoId":"…", "status":"Processing" }
413 type=image-too-large
415 type=unsupported-media-type
```

```
GET /api/v1/catalog/photos/{photoId}
200 (Processing)  { "photoId","status":"Processing" }
200 (Completed)   { "photoId","status":"Completed",
                    "detectedBasis":"Per100g",
                    "detectedProductName":"Skyr Protein Pudding Vanille",
                    "fields": {
                      "kcal":   { "value":184,  "confidence":0.97 },
                      "fat":    { "value":9.2,  "confidence":0.95 },
                      "saturatedFat": { "value":5.8, "confidence":0.78 },
                      "carbs":  { "value":3.1,  "confidence":0.93 },
                      "sugar":  { "value":2.9,  "confidence":0.64 },
                      "protein":{ "value":21.0, "confidence":0.96 },
                      "salt":   { "value":null, "confidence":0.0 } } }
200 (Failed)      { "photoId","status":"Failed","failureReason":"unreadable" }
404 type=photo-not-found
```

```
POST /api/v1/catalog/products
Header Idempotency-Key
Body { "id":"<client-guid>", "barcode":"4008400401027", "name":"…", "brand":null,
       "basisUnit":"Gram", "sourcePhotoId":"…",
       "nutrientsPer100": { "kcal":184,"fat":9.2,"saturatedFat":5.8,
                            "carbs":3.1,"sugar":2.9,"protein":21.0,"salt":0.14 } }
201 { …Produkt… }
400 type=nutrients-invalid   errors: { "nutrientsPer100.kcal": ["Pflichtfeld"] ,
                                       "nutrientsPer100.sugar":["Darf Kohlenhydrate nicht überschreiten"] }
409 type=barcode-already-public
```

```
PUT /api/v1/catalog/products/{id}      Header If-Match  → 200 | 403 | 409
```

---

## 3. Bounded Context: Diary (Tagebuch)

**Verantwortung.** Mahlzeiten-Slots, Tageseinträge, Tagesaggregation, Planung künftiger Tage.

### Aggregates

**`MealSlot` (Aggregate Root)** — `Id: MealSlotId`, `UserId: UserId`, `Name: SlotName` (1–40 Zeichen), `Position: SlotPosition` (0-basiert, nicht negativ), `IsArchived: bool`.
Invarianten: mindestens ein Slot pro Nutzer; `Position` lückenlos; Löschen eines Slots mit Einträgen ist **nicht** erlaubt (`409 slot-not-empty`) — der Client muss vorher verschieben oder löschen.

**`DiaryDay` (Aggregate Root, Schlüssel `UserId` + `Date: DiaryDate`)**
Enthält die Liste der `DiaryEntry` als Child-Entities. Ein Tag ist ein eigenes Aggregate, damit Tagessummen konsistent sind.

**`DiaryEntry` (Entity innerhalb `DiaryDay`)**

| Feld | Typ | Regel |
|---|---|---|
| `Id` | `DiaryEntryId` (Client-erzeugt) | |
| `MealSlotId` | `MealSlotId` | muss existieren und dem Nutzer gehören |
| `Source` | `EntrySource` — Union: `FromProduct(ProductId)` oder `FromRecipe(RecipeId, Portions)` | ersetzt das Paar `SourceType` + `SourceId`; eine `ProductId` kann nicht mehr in einem Rezept-Fall landen |
| `DisplayName` | `DisplayName` | zum Zeitpunkt der Erfassung eingefroren |
| `Amount` | `Grams` | > 0, ≤ 5000, im Value Object geprüft |
| `PortionLabel` | `PortionLabel?` | z. B. „150 g (1 Portion)" — reine Anzeige |
| `Nutrients` | `NutrientsPer100` | **Kopie** aus der Quelle zum Erfassungszeitpunkt |
| `CreatedAt`, `UpdatedAt` | `DateTimeOffset` | |

**Entscheidende Regel:** Nährwerte werden in den Eintrag **kopiert**, nicht referenziert. Ändert sich das Produkt später, bleiben vergangene Tage unverändert. Das ist bewusst so, nicht optimierbar.

Weitere Regeln:
- **Zusammenfassen gleicher Einträge:** Wird im selben Slot desselben Tages ein Eintrag mit identischer `SourceId` hinzugefügt, addiert das Aggregate die Gramm auf den bestehenden Eintrag statt eine zweite Zeile zu erzeugen. Antwort ist dann `200` mit dem zusammengefassten Eintrag.
- **Zukunft:** `Date` darf bis zu 14 Tage in der Zukunft liegen (Planung), beliebig weit in der Vergangenheit.
- **Verschieben:** `MealSlotId` eines Eintrags darf geändert werden (Drag & Drop im Client). Trifft er dabei auf einen gleichen Eintrag, gilt die Zusammenfass-Regel.

### Use Cases

`GetDay(date)`, `AddEntry`, `UpdateEntryAmount`, `MoveEntry(newSlotId)`, `DeleteEntry`, `ListSlots`, `CreateSlot`, `RenameSlot`, `ReorderSlots`, `DeleteSlot`.

### API-Contracts

```
GET /api/v1/diary/days/{date}          date = YYYY-MM-DD
200 {
 "date":"2026-08-04",
 "isPlanned": false,                         ← date > heute in der TZ des Nutzers
 "goal": { "kcal":2150, "carbsG":215, "proteinG":161, "fatG":72,
           "activityKcal":412, "activityIncluded":false, "effectiveKcal":2150 },
 "totals": { "kcal":615, "carbsG":47, "proteinG":81, "fatG":10 },
 "slots":[ { "slotId":"…","name":"Frühstück","position":0,
             "totals": { "kcal":318,"carbsG":41,"proteinG":25,"fatG":4 },
             "entries":[ { "id":"…","sourceType":"Product","sourceId":"…",
                           "displayName":"Haferflocken, zart","grams":60,
                           "portionLabel":"60 g",
                           "nutrientsPer100":{…},
                           "computed":{ "kcal":222,"carbsG":35,"proteinG":8,"fatG":4 } } ] } ],
 "activities":[ { "name":"Laufen","detail":"38 min · 7,2 km","kcal":264 } ]   ← aus HealthSync, leer wenn nicht verbunden
}
```
`computed` ist bereits nach der Rundungseinstellung des Nutzers gerundet (siehe Goals). `nutrientsPer100` bleibt ungerundet.

```
POST /api/v1/diary/days/{date}/entries
Header Idempotency-Key
Body { "id":"<client-guid>", "mealSlotId":"…", "sourceType":"Product",
       "sourceId":"…", "displayName":"Skyr Natur", "grams":150,
       "portionLabel":"150 g" }
201 { …Eintrag… }        Neuer Eintrag
200 { …Eintrag… }        Mit vorhandenem zusammengefasst (grams addiert)
400 type=grams-out-of-range
404 type=meal-slot-not-found | type=source-not-found
422 type=date-too-far-in-future    (> 14 Tage)
```

```
PATCH /api/v1/diary/days/{date}/entries/{entryId}
Body { "grams": 180 }            → 200 | 400 | 404
PATCH /api/v1/diary/days/{date}/entries/{entryId}/slot
Body { "mealSlotId": "…" }       → 200 (ggf. zusammengefasst) | 404
DELETE /api/v1/diary/days/{date}/entries/{entryId}   → 204 | 404
```

```
GET  /api/v1/diary/slots                 200 [ { "id","name","position" } ]
POST /api/v1/diary/slots                 Body { "id","name" }        → 201
PATCH /api/v1/diary/slots/{id}           Body { "name" }             → 200
PUT  /api/v1/diary/slots/order           Body { "slotIds":[ … ] }    → 200
DELETE /api/v1/diary/slots/{id}          → 204 | 409 type=slot-not-empty
```

```
GET /api/v1/diary/recent?take=10
200 [ { "sourceType":"Product","sourceId":"…","displayName":"Skyr Natur, Arla",
        "lastGrams":150,"lastUsedUtc":"…","kcalPerPortion":97 } ]
```
Liefert die zuletzt erfassten Produkte **und** Rezepte gemischt, absteigend nach letzter Verwendung. Der Client zeigt das als eine Liste „Letzte Einträge".

---

## 4. Bounded Context: Recipes (Rezepte)

**Verantwortung.** Nutzereigene Rezepte aus mehreren Zutaten, Portionierung, Ableitung der Nährwerte pro 100 g.

### Aggregates

**`Recipe` (Aggregate Root)** — `Id: RecipeId`, `UserId: UserId`, `Name: RecipeName` (1–80), `Portions: Portions` (> 0, Default 1, im Value Object geprüft), `Ingredients` (Liste, mind. 1 zum Speichern), `CreatedAt`/`UpdatedAt: DateTimeOffset`, `RowVersion`.

**`RecipeIngredient` (Entity)** — `Id: IngredientId`, `ProductId: ProductId`, `DisplayName: DisplayName` (eingefroren), `Amount: Grams`, `Nutrients: NutrientsPer100` (Kopie aus dem Produkt).

Berechnete Werte (Domain-Methoden, nicht persistiert):
```
TotalGrams   = Σ Ingredient.Grams
TotalKcal    = Σ (Ingredient.NutrientsPer100.Kcal × Grams / 100)      (analog je Makro)
GramsPerPortion = TotalGrams / Portions
NutrientsPer100 = TotalNutrients / TotalGrams × 100
```
**Regel:** Ein Rezept wird beim Speichern auf `NutrientsPer100` normalisiert. Genau diese Werte landen später als Kopie in einem Tagebucheintrag — ein Rezept verhält sich im Tagebuch damit exakt wie ein Produkt.

**Regel zur Herkunft von Zutaten:** Zutaten entstehen ausschließlich aus Produkten des Catalog-Contexts (Barcode-Treffer oder OCR-Erfassung). Es gibt keinen Endpunkt, der eine freie Zutat mit selbst getippten Nährwerten anlegt. Das ist eine Produktentscheidung und keine technische Einschränkung.

### Use Cases

`ListRecipes(sort)`, `GetRecipe`, `CreateRecipe`, `UpdateRecipe`, `DeleteRecipe`, `AddIngredient`, `UpdateIngredientGrams`, `RemoveIngredient`.

### API-Contracts

```
GET /api/v1/recipes?sort=name_desc            sort: name_asc | name_desc | recent
200 [ { "id","name","portions":4,
        "totalGrams":1350,"gramsPerPortion":338,
        "kcalPerPortion":412,
        "nutrientsPer100":{ "kcal":122,"fat":3.1,"carbs":14.2,"protein":9.8 } } ]
```

```
GET  /api/v1/recipes/{id}
200 { …wie oben…, "ingredients":[ { "id","productId","displayName":"Basmatireis, roh",
                                    "grams":320,"nutrientsPer100":{…},
                                    "computedKcal":1117 } ] }

POST /api/v1/recipes            Header Idempotency-Key
Body { "id":"<client-guid>","name":"Hähnchen-Reis-Pfanne","portions":4,
       "ingredients":[ { "id":"…","productId":"…","grams":600 } ] }
201 { …Rezept… }
400 type=recipe-needs-ingredient     (leere Zutatenliste)
400 type=portions-invalid            (≤ 0)

PUT    /api/v1/recipes/{id}     Header If-Match   → 200 | 409
DELETE /api/v1/recipes/{id}                       → 204
```

```
POST /api/v1/recipes/{id}/portions-to-diary
Body { "date":"2026-08-04", "mealSlotId":"…", "amount":1, "unit":"Portion" }
      unit: "Portion" | "Gram"
201 { "entryId":"…" }        → ruft intern Diary.AddEntry mit sourceType=Recipe
404 type=recipe-not-found | type=meal-slot-not-found
```

---

## 5. Bounded Context: Goals & Preferences (Ziele und Einstellungen)

**Verantwortung.** Tagesziel, Makroverteilung, Berechnungs- und Rundungsregeln, Darstellungseinstellungen. Dieser Context beantwortet die Frage „nach welchen Regeln rechnet die App".

### Aggregates

**`NutritionGoal` (Aggregate Root, eins pro Nutzer)**

| Feld | Typ | Regel |
|---|---|---|
| `DailyEnergy` | `DailyKcal` | 800–8000, im Value Object geprüft |
| `Distribution` | `MacroDistribution` (drei `Percentage`) | hält die drei Anteile zusammen und weiß, ob die Summe 100 ergibt — die Regel liegt am Typ, nicht im Service |
| `Factors` | `EnergyFactors` (Union: `Physiological`, `Declaration`) | Default `Physiological`; die Faktoren sind Verhalten des Falls, keine Tabelle daneben |
| `Rounding` | `RoundingDirection` (Union: `Up`, `Down`) | Default `Up`; jeder Fall implementiert `Apply(decimal) → int` selbst |
| `IncludeActivityInGoal` | `bool` | Default **false** |

**Brennwerte (fest verdrahtet, nicht konfigurierbar):**
- `Physiological` (Atwater): Kohlenhydrate 4,1 · Eiweiß 4,1 · Fett 9,3 kcal/g
- `Declaration` (VO (EU) Nr. 1169/2011, Anhang XIV): 4 · 4 · 9 kcal/g

**Rundung:** Ausgaben sind **immer ganzzahlig**, nie kaufmännisch — entweder durchgehend aufgerundet (`Math.Ceiling`) oder abgerundet (`Math.Floor`), je nach `RoundingDirection`. Dies gilt für jede berechnete Ausgabe der API (Tagessummen, `computed`-Blöcke, Portionswerte). Nährwerte pro 100 g bleiben ungerundet.

**Konsistenzregel Prozente (wichtig für das UI):** Die Prozentsumme **darf** vorübergehend ungleich 100 sein — das ist ein gültiger Zwischenzustand, kein Fehler. Das Backend speichert ihn und liefert `percentSum` mit. Nur wenn die Summe exakt 100 ist, rechnet der Server `DailyKcal` aus den Gramm neu. Ein `400` wegen einer Summe ≠ 100 darf es **nicht** geben.

Ableitung Gramm ⇄ Prozent:
```
GrammX = DailyKcal × PercentX / 100 / FaktorX
PercentX = (GrammX × FaktorX) / DailyKcal × 100
```

**`AppPreferences` (Aggregate Root, eins pro Nutzer)** — `Theme` (Union: `Dark`, `Light`; Default `Dark`), `Language` (Union: `German`, `English`), `MeasurementSystem` (Union: `Metric`).

### API-Contracts

```
GET /api/v1/goals
200 { "dailyKcal":2150,
      "macros": { "carbs": { "percent":40,"grams":215,"kcal":882 },
                  "protein":{ "percent":30,"grams":161,"kcal":661 },
                  "fat":    { "percent":30,"grams":72, "kcal":670 } },
      "percentSum":100,
      "energyFactors":"Physiological",
      "factors": { "carbs":4.1,"protein":4.1,"fat":9.3 },
      "roundingDirection":"Up",
      "includeActivityInGoal":false }

PUT /api/v1/goals
Body (jedes Feld optional, Server rechnet die übrigen nach den Regeln oben nach)
     { "dailyKcal":2200 }
     { "macros": { "carbs": { "percent":50 } } }
     { "macros": { "protein": { "grams":180 } } }
     { "energyFactors":"Declaration", "roundingDirection":"Down",
       "includeActivityInGoal":true }
200 (wie GET)
400 type=daily-kcal-out-of-range
```

```
GET   /api/v1/preferences        200 { "theme":"Dark","language":"de" }
PATCH /api/v1/preferences        Body { "theme"?, "language"? } → 200
```

---

## 6. Bounded Context: HealthSync (Apple Health / Health Connect)

**Verantwortung.** Entgegennahme der Aktivitätsdaten vom Gerät und Bereitstellung für die Tagesansicht. Das Backend spricht **nicht** selbst mit HealthKit — das Gerät liest die Daten und liefert sie hier ab.

### Aggregates

**`DailyActivity` (Aggregate Root, Schlüssel `UserId` + `Date: DiaryDate`)** — `Entries` (Liste `ActivityEntry { ExternalActivityId Id, ActivityName Name, ActivityDetail Detail, Energy Kcal, DateTimeOffset StartedAt, DateTimeOffset EndedAt }`), `TotalKcal` (berechnet), `LastSyncedAt: DateTimeOffset`.
Invariante: `ExternalId` je Tag eindeutig ⇒ wiederholtes Hochladen desselben Workouts erzeugt keine Dubletten (Upsert).

**`HealthConsent` (Aggregate Root)** — `UserId`, `Connection` (Union: `NotConnected`, `Connected(DateTimeOffset Since)`), `ImportActivity` (bool), `ExportNutrition` (bool), `UpdatedAt: DateTimeOffset`.
Hinweis: Das ist nur die Spiegelung der In-App-Schalter für die Serverlogik. Die tatsächlichen Systemfreigaben verwaltet das Betriebssystem.

### API-Contracts

```
PUT /api/v1/health/activity/{date}
Body { "entries":[ { "externalId":"HK-…","name":"Laufen",
                     "detail":"38 min · 7,2 km","kcal":264,
                     "startUtc":"…","endUtc":"…" } ] }
200 { "date":"2026-08-04","totalKcal":412,"entries":[ … ] }

GET /api/v1/health/activity/{date}     200 (wie oben)

GET   /api/v1/health/consent           200 { "connected":true,"importActivity":true,"exportNutrition":true }
PATCH /api/v1/health/consent           Body { "connected"?,"importActivity"?,"exportNutrition"? } → 200
```

```
GET /api/v1/health/nutrition-export/{date}
200 { "date":"…","kcal":615,"carbsG":47,"proteinG":81,"fatG":10 }
```
Der Client schreibt diese Werte anschließend selbst in HealthKit.

---

## 7. Sync-Endpunkt für den Offline-Betrieb

Die App muss im Supermarkt ohne Netz funktionieren. Dafür ein Endpunkt, der alle in der Warteschlange gesammelten Operationen in einem Rutsch entgegennimmt:

```
POST /api/v1/sync/batch
Body { "operations":[
        { "opId":"<guid>", "type":"diary.addEntry",
          "payload": { …identisch zum Einzel-Endpunkt… } },
        { "opId":"<guid>", "type":"catalog.createProduct", "payload": {…} } ] }
200 { "results":[ { "opId":"…","status":"applied","body":{…} },
                  { "opId":"…","status":"duplicate" },
                  { "opId":"…","status":"failed",
                    "problem": { …RFC7807… } } ] }
```
Regeln: Operationen werden **in der gesendeten Reihenfolge** verarbeitet; eine fehlgeschlagene Operation stoppt die Verarbeitung nicht; `opId` ist zugleich der Idempotency-Key. Unterstützte `type`-Werte: `diary.addEntry`, `diary.updateEntry`, `diary.moveEntry`, `diary.deleteEntry`, `catalog.createProduct`, `recipes.createRecipe`, `recipes.updateRecipe`, `health.putActivity`.

---

## 8. Reihenfolge der Umsetzung

1. Identity (Register/Login/Refresh) + Fehlerformat + Auth-Pipeline.
2. Goals (Default-Profil auf `UserRegistered`) — wird von Diary gebraucht.
3. Catalog: Produkt-Aggregat, Barcode-Suche, Textsuche, manuelles Anlegen.
4. Diary: Slots, Tag, Einträge, Tagesaggregation.
5. Catalog: Foto-Upload, OCR-Agent, Erfassung aus OCR.
6. Recipes.
7. HealthSync.
8. Sync-Batch.

## 9. Tests, die vorhanden sein müssen

- **Domain-Unit-Tests** je Aggregate für jede oben genannte Invariante (kein Mocking).
- **Value Objects:** je Typ ein Test, dass ein ungültiger Wert beim Erzeugen scheitert — und ein Architekturtest (NetArchTest), der sicherstellt, dass kein Aggregate ein fachliches `string`/`int`/`decimal`/`Guid`-Feld trägt, dass in der Domäne kein `enum` deklariert ist und dass `DateTime` im gesamten Lösungspfad nicht vorkommt.
- **Unions:** je Union ein Test, der alle Fälle serialisiert und wieder einliest (Diskriminator-Stabilität), damit gespeicherte Daten einen späteren Umbau überstehen.
- **Rundung:** `Up`/`Down` × beide Faktorensätze über eine Tabelle bekannter Werte; Assertion, dass **nie** eine Nachkommastelle in einer berechneten Ausgabe erscheint.
- **Zusammenfassen:** zweimal dasselbe Produkt in denselben Slot ⇒ ein Eintrag mit addierten Gramm.
- **Kopiersemantik:** Produkt nach dem Eintrag ändern ⇒ alter Tagebucheintrag unverändert.
- **Idempotenz:** derselbe `Idempotency-Key` zweimal ⇒ ein Datensatz, zweite Antwort `200`.
- **Integrationstests** über `WebApplicationFactory` gegen PostgreSQL in Testcontainers für jeden Endpunkt inklusive der dokumentierten Fehlerfälle.
