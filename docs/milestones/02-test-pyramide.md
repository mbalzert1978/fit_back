# Test-Pyramide

Ergänzt BACKEND.md Abschnitt 9 („Tests, die vorhanden sein müssen") um eine explizite Ebene für
die Kommunikation zwischen den Bounded Contexts. Abschnitt 9 selbst bleibt unverändert gültig für
alles, was er bereits abdeckt (Domain-Unit-Tests, Value-Object-Tests, Architekturtests,
Union-Serialisierungstests, Rundungstests, Idempotenz, Integrationstests) — diese Datei fügt nur
die fehlende Ebene ein und ordnet sie gegenüber den bestehenden ab.

Grundlage: [Contract Tests](https://martinfowler.com/articles/practical-test-pyramid.html#ContractTests)
(Fowler, *Practical Test Pyramid*) — Consumer-Driven-Contracts-Prinzip: der Konsument einer
Schnittstelle formuliert, was er von ihr braucht, der Anbieter führt genau diese Erwartungen
kontinuierlich gegen seine eigene Implementierung aus. Das entkoppelt beide Seiten von teuren,
brüchigen Ende-zu-Ende-Verfahren, ohne auf Absicherung der Schnittstelle zu verzichten.

## Die vier Ebenen dieses Projekts

```
        ▲  Manuell/Smoke   docker compose up + curl (siehe 01-technical-decisions.md)
        │
        │  Integrationstests   Testcontainers-Postgres, echte DB/Blob/Queue, ein Context,
        │                      alle Endpunkte + dokumentierten Fehlerfälle (Abschnitt 9)
        │
        │  Contract-Tests      Modul-zu-Modul-Grenze, kein Netzwerk/DB, beide Seiten prüfen
        │                      dieselbe Erwartung (NEU — dieses Dokument)
        │
        ▼  Domain-Unit-Tests   je Aggregate/Value-Object/Union, kein Mocking (Abschnitt 9)
```

Contract-Tests sitzen bewusst **zwischen** Unit- und Integrationstests: schmaler im Umfang als ein
Integrationstest (keine echte Datenbank, kein laufender zweiter Prozess), aber breiter als ein
Unit-Test, weil sie tatsächlich eine Schnittstelle zwischen zwei Contexts prüfen, nicht nur eine
einzelne Aggregat-Invariante.

## Warum diese Ebene in einem modularen Monolithen trotzdem nötig ist

Fowler beschreibt Contract Tests für Schnittstellen zwischen separat deployten Services. Dieses
Projekt ist aktuell ein Monolith — aber die Cross-Context-Kommunikationsregel aus
[01-technical-decisions.md](./01-technical-decisions.md) wurde exakt so entworfen, dass jede
Modulgrenze bereits **wie** eine künftige Service-Grenze aussieht (aufrufer-eigenes `Protocol`-Port
für synchrone Aufrufe, Postgres-Outbox-Events für asynchrone Reaktionen). Contract-Tests sichern
genau diese beiden Seemarken ab — und zahlen sich doppelt aus: heute verhindern sie, dass ein
Context die Erwartungen eines anderen unbemerkt bricht; am Tag einer Extraktion sind sie bereits
die Tests, die (nur mit einem echten statt einem In-Process-Adapter) unverändert weiterlaufen.

## Drei Schnittstellenarten, drei Contract-Test-Formen

### A) Synchrone Aufrufe über ein aufrufer-eigenes Port (`Protocol`)

Betrifft z. B. `Recipes.DiaryGateway` (Ticket 0038) und `Diary.HealthActivityGateway` (Ticket
0042). Der **Konsument** (der Context, der das Port definiert) schreibt eine einzige,
implementierungsunabhängige Test-Suite gegen das `Protocol` selbst — eine Funktion wie
`assert_diary_gateway_contract(gateway: DiaryGateway) -> None`, die alle vom Konsumenten
benötigten Fälle prüft (Erfolgsfall, jeder dokumentierte Fehlerfall). Diese Suite liegt im
Konsumenten-Context (`contexts/<consumer>/specs/contracts/`), wird aber vom **Anbieter**
importiert und gegen dessen eigenen In-Process-Adapter ausgeführt — der Anbieter weiß nichts vom
Konsumenten, führt aber dessen Erwartungen kontinuierlich in seiner eigenen Testsuite mit aus. Bei
einer späteren Extraktion ersetzt nur der Adapter (In-Process → HTTP/gRPC-Client) das
Prüfobjekt; die Contract-Suite selbst bleibt unverändert.

### B) Die HTTP-Grenze — Pact, consumer-driven vom Frontend

Der Rand nach außen ist durch die Pact-Verträge des Frontends gedeckt, nicht durch selbst
geschriebene Erwartungen: die Vertragsdateien liegen unter `contracts/pacts/<context>/`, die
Provider-Verifikation als Test unter `tests/contracts/`. Sie fährt die App unter `uvicorn` hoch und
spielt die Interaktionen des jeweiligen Vertrags dagegen ab; jeder Vertrag bekommt einen eigenen
Lauf unter seinem Provider-Namen. Ein Endpunkt, der noch nicht gebaut ist, bleibt über einen
sichtbaren Filter draußen, bis sein Ticket kommt. Begründung und Reichweite:
[`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`](../decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md).

Weil der Vertrag vom Konsumenten kommt, ist er **Vorgabe**, nicht Nachweis: was dort steht, ist die
Zielform der Schnittstelle, und ein roter Lauf heißt „noch nicht gebaut", nicht „falsch getestet".

### C) Asynchrone Integration Events über die Postgres-Outbox — offen

Betrifft z. B. `UserRegistered` (Ticket 0011), `UserDeletionRequested`/`UserDeleted` (Ticket
0017), sowie deren Konsumenten (`Goals`-Default-Profil Ticket 0018, `Diary`-Standard-Slots Ticket
0026). **Hier ist keine Form entschieden.** Der früher an dieser Stelle beschriebene Mechanismus —
kanonische Beispiel-Payloads je Event-Fall unter
`contexts/<producer>/contracts/events/<event>/examples/*.json` plus Roundtrip-Test beim Anbieter
und beim Konsumenten — ist zurückgenommen worden und hat keinen Nachfolger. Pact deckt ihn nicht
ab: dessen Umfang ist ausdrücklich die HTTP-Grenze, und Context-zu-Context-Ereignisse laufen heute
in einem Prozess. Bis eine Form entschieden ist, ist die Feldmenge veröffentlichter Ereignisse nur
durch die Slice-Specs des Anbieters gedeckt.

## Abgrenzung zu den bestehenden Ebenen

| Ebene | Prüft | Braucht echte Infrastruktur? | Kennt die andere Seite? |
|---|---|---|---|
| Domain-Unit-Test (Abschnitt 9) | Eine Invariante eines Aggregats/VOs/Unions | Nein | Nein — kein Context-übergreifender Bezug |
| **Contract-Test (neu)** | Eine Schnittstelle nach außen (Pact) oder zwischen zwei Contexts (Port/Event) | Nur für Form B (Pact fährt die App hoch); A und C nein | Ja, aber nur über den Vertrag bzw. das Port/Event-Schema, nie über Domain-/ORM-Interna |
| Integrationstest (Abschnitt 9) | Ein Context Ende-zu-Ende inkl. echter Postgres/Blob/Queue | Ja (Testcontainers) | Nein — ein Context pro Testlauf |
| Manuell/Smoke | Das Gesamtsystem über HTTP | Ja (Docker Compose) | Ja, aber ungeprüft/explorativ, kein automatisiertes Gate |

Ein Integrationstest, der zwei Contexts gemeinsam hochfährt, um ihre Kommunikation zu prüfen, wäre
nach dieser Einordnung ein **Antipattern** hier: langsamer, brüchiger, und er verschiebt den
Fehlerort vom eigentlichen Schnittstellenbruch weg. Wo bisher ein Milestone-Dokument
„Integrationstest End-to-End über Context A + B" als Testanforderung nennt (z. B. M2, M4, M6,
M7), gilt ab sofort: der Schnittstellenanteil davon ist ein Contract-Test (Ebene A bzw. C), der
verbleibende Rest bleibt ein normaler Integrationstest **innerhalb eines** Context.

## Nicht betroffen: Sync-Batch (M8)

Der Sync-Batch-Dispatcher (Tickets 0043–0045) ruft keine Context-fremden Ports auf, sondern
denselben Application-Service, den auch der jeweilige Einzel-Endpunkt nutzt (siehe
`m8-sync-batch.md`, „Architektur-Hinweis") — das ist Presentation-Layer-Orchestrierung über
bereits vorhandene, bereits contract-getestete Application-Schnittstellen, keine neue
Context-zu-Context-Kopplung. Für M8 bleibt es bei Unit- und Integrationstests.

## Auswirkung auf bestehende Tickets

Folgende bereits angelegte Tickets erhalten ein zusätzliches Akzeptanzkriterium für ihren
Contract-Test-Anteil (Details dort): 0011, 0017, 0018, 0026, 0038, 0042.
