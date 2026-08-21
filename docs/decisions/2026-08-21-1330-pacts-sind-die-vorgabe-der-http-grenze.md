# Die Pact-Verträge des Frontends sind die Vorgabe der HTTP-Grenze

**Datum:** 2026-08-21, 13:30
**Anlass:** Vorgabe des Stakeholders, künftig gegen die Verträge zu bauen statt gegen
[`docs/Draft/BACKEND.md`](../Draft/BACKEND.md). Durchgegrillt in einer `/wayfinder`-Sitzung am
2026-08-21; eine Map ist bewusst **nicht** angelegt worden — nach der Klärung blieb nichts mehr zu
entscheiden, sondern nur noch zu bauen (dieselbe Lage wie bei
[#94](https://github.com/mbalzert1978/fit_back/issues/94)).

## 1. Wofür die Verträge Autorität sind

**Die Verträge binden die HTTP-Grenze — Pfade, Statuscodes, Header, Feldnamen, Antwortform.**
Sie sind Autorität für alles unter `src/api/**`.

`BACKEND.md` bleibt Autorität für Domäne, Invarianten, Ereignisse und Persistenz. Ein Vertrag redet
über die Leitung; er sagt nichts über Aggregate. Wo er dennoch eine Domänenfrage entscheidet, tut er
das durch Bauart (siehe Punkt 4), nicht durch Vorschrift.

**Wo beides kollidiert, gewinnt der Vertrag, und die Invariante wird nachgezogen — nicht der
Vertrag.** Der Konflikt wird in dem Ticket geklärt, das die betroffene Interaktion baut, nicht
vorab und nicht per Rückfrage an den Consumer.

## 2. Gebaut wird nur, was ein Vertrag deckt

Kein Endpunkt ohne Vertragsausschnitt. Der Entwurf läuft **outside-in**: vom Kopf in die Domäne.

**Eine benannte Ausnahme:** consumer-unsichtbare Querschnittsarbeit — Rate-Limiting, Cleanup-Jobs,
Betriebsthemen. Kein Consumer kann sie je beschreiben, weil er sie nicht sieht. „Nur was ein Vertrag
deckt" darf nicht „kein Rate-Limiting" heißen.

Fläche ohne Vertrag wird **geparkt**, nicht gebaut und nicht geschlossen: Sie kommt wieder, sobald
der Consumer sie beschreibt.

## 3. Baureihenfolge

Sie kippt auf `src/api/` (aus dem Vertrag) → `application/` → `domain/` → Test-API + Specs →
`infrastructure/`. Nachgezogen in
[`.rules/python/python-feature-slices.md`](../../.rules/python/python-feature-slices.md).

**Unangetastet bleibt die Abhängigkeitsrichtung.** `domain/` importiert nichts nach außen, der Slice
ist ohne Infrastruktur vollständig grün, `import-lint` gilt unverändert. Outside-in beschreibt, *wo
der Entwurf anfängt*, nicht *wer wen importieren darf*.

## 4. Der Kalendertag gehört dem Client

Aufgeworfen als Rückfrage aus dem Frontend: Der Client bestimmt seinen Kalendertag lokal. Leitet das
Backend ihn ebenfalls aus `User.TimeZoneId` ab, driften beide auseinander, sobald das Gerät die Zone
wechselt oder die Zone am Konto veraltet.

Gemessen: Jede Tagebuch-Route trägt den Tag im Pfad (`/api/v1/diary/days/2026-08-04`), lesend wie
schreibend. Der Vertrag gibt dem Server **keinen Kanal**, den heutigen Tag des Geräts zu erfahren —
kein Header, kein Query-Parameter. `timeZoneId` wird genau einmal übertragen, bei der Registrierung,
und nie wieder aufgefrischt.

**Entschieden:**

- Das Backend leitet aus `timeZoneId` **keinen Kalendertag** ab.
- `isFuture` verlässt den Vertrag — es ist eine Ableitung aus zwei Werten, die der Client beide hat.
- Die Schreibsperre „höchstens 14 Tage in der Zukunft" bleibt serverseitig, misst aber gegen das
  **UTC-Datum mit einem Tag Toleranz**. Reale Zonen liegen zwischen −12:00 und +14:00; das lokale
  Datum weicht vom UTC-Datum nie um mehr als einen Tag ab. Abgewiesen wird, was mehr als 15 Tage
  vor dem UTC-Datum liegt.
- `timeZoneId` bleibt Stammdatum — für Zeitpunkte, Auswertungen und Hintergrundjobs.

Damit fällt Querschnitts-Regel 4 aus `BACKEND.md` in ihrer heutigen Form.

## 5. Der Vertrag ist Mindestform, nicht Exaktform

Pact prüft Antwort-Bodies als Teilmenge und arbeitet mit Typ-Matchern, nicht mit Literalen.
Bindend sind Struktur und die Felder, für die kein Matcher gesetzt ist; der Wortlaut ist frei.

- **Erfolgs-Bodies** exakt nach Vertrag — nichts darüber hinaus, sonst driften sie still zu Formen
  zurück, die kein Consumer liest.
- **Fehler-Bodies** dürfen `detail`, `instance` und `errors` zusätzlich tragen: RFC 7807 definiert
  sie, und die i18n-Ressourcen aus M0 füllen sie bereits.

## 6. Unverhandelbar — in eine Richtung

**Das Backend ändert einen Vertrag nie einseitig** und baut nie gegen etwas anderes als die im Repo
liegende Datei. Es fordert auch keine Änderung an: Passt eine Vertragsvorgabe nicht zur Domäne, wird
die Domäne angepasst (Punkt 1).

Eine Rückfrage des Consumers ist ein legitimer Kanal — die Zeitzonen-Klärung in Punkt 4 ist so
entstanden. Ihr Ergebnis baut der Consumer ein und liefert es als neu erzeugte Vertragsdatei; erst
danach baut das Backend.

## 7. Wie die Verträge ins Repo kommen

- Ablage: **`contracts/pacts/<context>/`** im Repo-Root, mit Herkunftsnotiz je Vertrag (Quell-Commit,
  „go"-Datum). Sie sind weder Test noch Dokumentation, sondern Vorgabe, und werden von zwei Seiten
  gelesen: von der Verifikation und von jedem Ticket-Body, der einen Ausschnitt zitiert.
- **Kein Zugriff auf das Frontend-Repo.** Kein Submodul, kein CI-Job, kein Broker.
- **„Final" heißt: der Stakeholder gibt das „go" und legt die Datei selbst ab.** Das „go" gilt **je
  Vertrag**, nicht global — Identity kann fertig sein, während Diary noch wandert.
- Weicht eine spätere Fassung ab, ist das ein eigener Ticket-Anlass, kein stiller Nachzug.

Der Grund für diese Härte ist gemessen: Während der Klärungssitzung wurden die Vertragsdateien
**viermal** neu erzeugt und wuchsen von 33 auf 45 Interaktionen; der Identity-Vertrag ging von 4
über 7 auf 11 Interaktionen, `register` und `/me` kamen dabei erst dazu und das Fehlerformat wechselte
zweimal. Ohne einen erklärten Zeitpunkt ist „harte Vorgabe" nur so hart wie der Kopierzeitpunkt.

## 8. Was mit dem Bestand passiert

- **Keine Massenumschrift der offenen Tickets.** Jedes Ticket wird **beim Aufgreifen** gegen seinen
  Vertragsausschnitt neu geschrieben; fehlende Fläche wird dann als neues Ticket geschnitten.
- **`POST /register` zuerst, vor allem anderen.** Ein einziges Ticket trägt alles, was der Endpunkt
  braucht — Token-Ausstellung, Antwort-Envelope als Middleware, Fehlerform, Route. Es ist die
  **Referenz-Implementierung**, an der jedes folgende Ticket Maß nimmt, und wird gemeinsam mit dem
  Stakeholder gebaut, nicht von der Ticket-Pipeline.
- **`BACKEND.md`** verliert die Autorität über die HTTP-Form und trägt dazu einen Kopfvermerk.

## Was dadurch ausgeschlossen wird

- Kein Endpunkt mehr aus `BACKEND.md` heraus, wenn ein Vertrag dieselbe Fläche beschreibt.
- Keine Vertragsänderung auf Zuruf des Backends.
- Kein Bau gegen eine Vertragsfassung ohne „go".
- Kein zweiter Ablageort für Verträge neben `contracts/pacts/`.
