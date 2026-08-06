# Die Outbox ist ein Mechanismus, keine Naht

**Getroffen:** 2026-08-06, 11:20 — beim Neubau von Ticket 0010 innerhalb von Ticket 0011.

## Was entschieden wurde

Der Weg eines Integration Event vom Handler bis in die Datenbank hat **vier** Stufen, und
`src/shared_infrastructure/outbox/` ist die letzte davon — nicht die erste:

```
Handler → Domain-Port (shared_kernel) → Adapter (slice) → Naht (slice/abstractions) → Infrastruktur
```

1. **Domain-Port**, `src/shared_kernel/events.py`: `EventPublisher` mit
   `async publish(event: DomainEvent) -> None`. Der Handler kennt nur diesen.
2. **Domänen-Ereignis** im jeweiligen Context (`identity/domain/events.py`), typisiert über Value
   Objects. `to_payload()` entscheidet, welcher Ausschnitt den Context verlässt.
3. **Adapter** im Slice (`adapters/event_publisher_adapter.py`) — implementiert den Domain-Port,
   übersetzt in Primitive.
4. **Naht** im Slice (`abstractions/event_log.py`) — schmal, nur Primitive, vom Use Case
   formuliert.
5. **Erfüllung** in `shared_infrastructure/outbox/publishers/` — eine dünne Klasse je Naht, die
   `write_event` aufruft.

`shared_infrastructure/outbox/` deklariert dabei **keine** Schnittstelle, die ein Slice zu
erfüllen hätte. Es ist die Bibliothek, die Stufe 5 benutzt — dieselbe Rolle, die `idna` für die
E-Mail-Prüfung spielt.

## Warum

Der erste Anlauf legte die Naht (`PendingEvent`, `OutboxDispatch`) in die Infrastruktur und ließ
sie von dort aus vorgeben, was ein Handler zu sprechen hat. Das ist dieselbe Richtungsumkehr, die
schon beim IDN-Encoder korrigiert werden musste (siehe
[`exp_infrastruktur-erfuellt-naht-adapter-implementiert-port`](../reflections/exp_infrastruktur-erfuellt-naht-adapter-implementiert-port.md)),
nur eine Ebene höher: nicht die Infrastruktur beschreibt den Bedarf, sondern der Aufrufer.

Der Einwand, `shared_infrastructure` könne die `abstractions/` von sechs Contexts nicht
importieren, ohne die Abhängigkeitsrichtung umzudrehen, war **falsch**. Der `forbidden`-Contract
in `setup.cfg` listet nur die sechs Contexts als `source_modules`; Infrastruktur darf nach oben
greifen. Das ist die gewohnte Richtung aus .NET — ein Infrastructure-Projekt referenziert die
Application-Projekte und implementiert deren Interfaces, nie umgekehrt. Der Preis sind viele
winzige Klassen; jede davon ist zwei Zeilen lang und enthält keine Logik.

## Die Rückrichtung läuft über eine Registry

Wen der Relay beliefert, gibt er **nicht** vor. `EventRegistry` (ebenfalls
`src/shared_kernel/events.py`) bietet `register(event_type, handler)`; die Pipeline eines
reagierenden Use Case trägt sich dort beim Aufbau ein, der Relay schlägt nur nach. Damit kennen
sich beide Seiten nicht.

Mehrere Handler je Event-Typ sind der Normalfall, nicht die Ausnahme — auf `UserRegistered`
reagieren Goals *und* Diary. Die Registry ist eine Instanz und kein Modul-Global: Registrierungen
gehören zur Verdrahtung einer Anwendung, nicht zum Importzustand des Prozesses.

## `publish` hat keinen Fehlerkanal

`EventPublisher.publish` gibt `None` zurück, nicht `Result[None, E]`. Das Ereignis entsteht in
derselben Transaktion wie der Aggregate-Write; den Ausgang „Aggregat gespeichert, Ereignis
abgelehnt" gibt es fachlich nicht. Ein `Result` hätte hier genau einen Fall, den niemand erreichen
kann, und jeden Aufrufer gezwungen, ihn trotzdem zu behandeln — derselbe erfundene Fehlerfall wie
seinerzeit `WriteCollision`, siehe
[`exp_keine-vorpruefung-wo-die-gegenseite-entscheidet`](../reflections/exp_keine-vorpruefung-wo-die-gegenseite-entscheidet.md).
Ein Datenbankausfall ist kein Rückgabewert; er reißt die Transaktion ohnehin ab.

## `Result.inspect_async` als Konsequenz

Der Handler meldet nur den tatsächlich aufgenommenen User — ein Erfolg löst eine Nebenwirkung aus,
ohne dass die Nebenwirkung zum Ergebnis wird. Weder `map` (ersetzt den Wert) noch `bind` (ersetzt
den Ausgang) drücken das aus, also blieb nur ein Match über beide Fälle, dessen `Err`-Zweig das
Result unverändert durchreicht — Zeremonie für nichts.

`Ok`/`Err` haben deshalb `inspect_async(f)`: führt `f` auf dem Erfolgs-Wert aus, verwirft dessen
Rückgabewert und gibt das Result unverändert zurück; auf `Err` passiert nichts. Der Handler
schrumpft damit auf `return await registered.inspect_async(self._announce)`.

## Was der Mechanismus anders macht als der geschlossene PR #10

Branch `0010` diente als SQL-Vorlage. Fünf seiner Entscheidungen wurden umgedreht:

| PR #10 | jetzt |
|---|---|
| Relay liegt in `shared_kernel`, importiert ein ORM-Modell | alles in `shared_infrastructure/outbox/`, kein ORM |
| NOTIFY **ist** die Zustellung (mit handgebautem Quote-Escaping im SQL-String) | NOTIFY ist das Weckzeichen; zugestellt wird die per `SKIP LOCKED` geholte Zeile |
| Zeitstempel als `timestamptz` | `bigint` Unix-Sekunden, siehe [`2026-08-06-1340`](2026-08-06-1340-unix-epoch-statt-datetime.md) |
| Backoff als `asyncio.sleep` unter gehaltenen Row-Locks | Backoff als Zustand in `next_attempt_at` |
| `processed_at` auch nach erschöpften Retries gesetzt | eigene Spalte `failed_at`; aufgeben ≠ zugestellt |

Kein ORM-Modell, weil `alembic/env.py` mit `target_metadata = None` arbeitet: es gibt kein
Autogenerate, für das ein Modell nötig wäre, und der Import eines solchen war in PR #10 genau der
Weg, über den Infrastruktur in den `shared_kernel` geriet. Die Statements stehen als
`text()`-Konstanten im Relay, wo das SQL lesbar bleibt.

## Schema heißt `shared_kernel`, nicht `shared`

`CLAUDE.md` und Ticket 0010 sprechen von `shared.outbox`. Angelegt wird von
`alembic/shared/versions/001` tatsächlich das Schema `shared_kernel`; die Tabelle folgt dem
Bestand statt ein achtes Schema aufzumachen. Soll die Doku recht behalten, ist das eine Umbenennung
in den Migrationen 001/002 und keine Änderung an der Outbox.

## Zustellgarantie

**At-least-once.** Zustellung und Statuswechsel liegen in einer Transaktion; bricht der Prozess
dazwischen ab, verfällt die Sperre und das Event ist wieder fällig. Scheitert einer von mehreren
Handlern, gilt das ganze Event als nicht zugestellt und wird später erneut *allen* Handlern
angeboten — Reaktionen müssen deshalb idempotent sein. Zustellzustand je Handler zu führen lohnt
sich erst, wenn ein Event viele teure Reaktionen hat.
