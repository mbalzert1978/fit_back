# fit_back

Backend für Ernährungs-Tracking. Diese Datei hält die **Begriffe** dieses Repos: welches Wort für
eine Sache gilt und welche Wörter dafür nicht benutzt werden.

Sie ist ein Glossar und sonst nichts. Wie eine Sache gebaut ist, steht genau einmal, hinter dem
Link am Ende des Eintrags — die Struktur in [`docs/architecture.md`](docs/architecture.md), die
Form eines Slice in [`.rules/python/`](.rules/python/README.md). Ein Eintrag hier legt nur das
**Wort** fest.

**Jeder Eintrag geht auf einen im Repo dokumentierten Streitfall zurück.** Ein Begriff kommt hinzu,
wenn ein Ticket ihn schärft — nicht auf Vorrat
([2026-08-13-1221](docs/decisions/2026-08-13-1221-claude-md-behauptet-nichts-mehr.md)).

## Language

### Ein Slice und seine Teile

**Slice**:
Ein Use Case samt allem, was nur er braucht — seine Naht, seine Adapter, seine Mapper, seine
Test-API. Die Einheit, in der dieses Repo baut und prüft.
_Avoid_: Feature, Modul, Service, Schicht
→ [Slice-Form verbindlich geklärt](docs/decisions/2026-08-06-0751-slice-form-test-api-baureihenfolge.md),
[kein vorauseilendes `shared`](docs/reflections/exp_kein-vorauseilendes-shared.md)

**Naht**:
Die schmale öffentliche Anforderung, die ein Use Case selbst nach außen formuliert; über sie wandern
nur Primitive. Sie gehört dem Use Case, nicht der Datenquelle.
_Avoid_: Gateway, Interface, Port
→ [Infrastruktur erfüllt die Naht, ein Adapter implementiert den Port](docs/reflections/exp_infrastruktur-erfuellt-naht-adapter-implementiert-port.md),
[Die Outbox ist ein Mechanismus, keine Naht](docs/decisions/2026-08-06-1120-outbox-mechanismus-statt-naht.md)

**Port**:
Eine Schnittstelle, die die Domäne für sich selbst vorgibt; sie spricht Domänentypen und den
Fehlertyp ihres Context.
_Avoid_: Repository-Interface, Gateway, Naht
→ [Infrastruktur erfüllt die Naht, ein Adapter implementiert den Port](docs/reflections/exp_infrastruktur-erfuellt-naht-adapter-implementiert-port.md)

**Adapter**:
Der Baustein, der einen Port implementiert und dabei zwischen der Naht und der Domäne übersetzt.
Zwischen einer fremden Bibliothek und der Domäne steht immer einer.
_Avoid_: Wrapper, Fassade, Service
→ [Infrastruktur erfüllt die Naht, ein Adapter implementiert den Port](docs/reflections/exp_infrastruktur-erfuellt-naht-adapter-implementiert-port.md)

**Test-API**:
Die ausgelieferte Bedienoberfläche eines Slice für alles, was ihn verhaltensseitig prüft — Teil des
Slice, nicht des Testcodes.
_Avoid_: Test-Fassade, Mock-Gerüst, Test-Helper
→ [Slice-Form verbindlich geklärt](docs/decisions/2026-08-06-0751-slice-form-test-api-baureihenfolge.md),
[Test-Facade-Check gestrichen](docs/decisions/2026-08-06-1800-qa-gate-coverage-statt-test-facade.md)

### Über die Grenzen eines Context

**Vertrag**:
Das veröffentlichte Vokabular eines Context — der einzige Teil, den ein fremder Context importieren
darf. Er trägt nur Primitive.
_Avoid_: DTO, Transport-DTO, Schema, öffentliche API
→ [Die Outbox ist ein Mechanismus, keine Naht](docs/decisions/2026-08-06-1120-outbox-mechanismus-statt-naht.md),
[Registrierung über den Vertragstyp](docs/reflections/exp_registrierung-ueber-den-vertragstyp.md)

**Pact-Vertrag**:
Der vom Frontend erzeugte, hier abgelegte Pact — die Vorgabe der HTTP-Grenze eines Context. Ein
anderes Ding als der **Vertrag** oben: der gehört diesem Repo und bindet Context an Context, der
Pact-Vertrag gehört dem Konsumenten und bindet die Außengrenze. Kurzform „Pact" ist in Ordnung,
das nackte Wort „Vertrag" für eine `.json`-Datei unter `contracts/pacts/` nicht.
_Avoid_: Contract, API-Contract, Schema
→ [Pacts sind die Vorgabe der HTTP-Grenze](docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md),
[Die Mechanik der Provider-Verifikation](docs/decisions/2026-08-21-1420-mechanik-der-provider-verifikation.md)

**Ereignis**:
Eine Tatsache, die ein Context veröffentlicht, nachdem sie eingetreten ist. Es existiert genau
einmal, als Vertrag — nicht als Paar aus Domänen-Ereignis und Transport-DTO.
_Avoid_: Message, Notification, Event-DTO
→ [Die Outbox ist ein Mechanismus, keine Naht](docs/decisions/2026-08-06-1120-outbox-mechanismus-statt-naht.md)

**Outbox**:
Der Zustellweg, über den ein veröffentlichtes Ereignis seine Empfänger erreicht. Ein Mechanismus,
den ein Slice benutzt — keine Naht, die er erfüllt.
_Avoid_: Bus, Broker, Queue
→ [Die Outbox ist ein Mechanismus, keine Naht](docs/decisions/2026-08-06-1120-outbox-mechanismus-statt-naht.md)

**Shared Kernel**:
Das Modell, das alle Contexts teilen; es hängt an nichts außer der stdlib.
_Avoid_: Common, Utils, Shared Infrastructure — kontextübergreifende Infrastruktur ist etwas
anderes und heißt hier nicht so ([`docs/architecture.md`](docs/architecture.md))
→ [Shared Infrastructure getrennt vom Shared Kernel](docs/decisions/2026-08-05-1245-shared-infrastructure-getrennt-von-shared-kernel.md),
[Neuschnitt des Shared Kernel](docs/decisions/2026-08-06-1330-shared-kernel-neuschnitt.md),
[kein vorauseilendes `shared`](docs/reflections/exp_kein-vorauseilendes-shared.md)

### Wenn etwas nicht gelingt

**Fachlicher Fehlausgang**:
Ein vorgesehener, benannter Ausgang eines Use Case, der kein Erfolg ist — ein Fall seiner
Response-Union.
_Avoid_: Fehler, Exception, Error
→ [Die Fehlernutzlast als typisierter Fall wird verbindliche Regel](docs/decisions/2026-08-07-0646-fehlernutzlast-als-typisierter-fall-ist-regel.md)

**Fehlercode**:
Der stabile Bezeichner eines Fehlausgangs; er steht auf dem Fall selbst.
_Avoid_: Fehlermeldung, Fehlertext — Text entsteht erst am HTTP-Rand
→ [Fehlercodes statt Prosa aus dem Slice](docs/decisions/2026-08-07-0634-fehlercodes-statt-prosa-aus-dem-slice.md),
[Die Menge der Fehlercodes wird abgeleitet](docs/decisions/2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md)
