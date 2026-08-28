# Die Sitzung entsteht im Handler — hinter Port und Adapter

## Was entschieden wurde

`session_step.py` ist weg. Die Ausstellung der Sitzung steht jetzt im Handler des Use Case
`register_user`, und sie geht durch dieselbe Naht-Adapter-Form wie jede andere Abhängigkeit:

| neu | was es ist |
|-----|------------|
| `domain/value_objects/session.py` | `Session` — die Sitzung auf der Innenseite |
| `domain/ports/session_issuer.py` | `SessionIssuer` — Protocol, spricht `User` und `Session` |
| `application/register_user/adapters/session_issuer_adapter.py` | ACL: übersetzt zur public Naht `RegisterUserSessionTokens` und zurück |

Geändert: `handler.py` (orchestriert die Ausstellung mit), `registration.py` (`session: Session`
statt `session: IssuedSession`), `pipeline.py` (verdrahtet nur noch).

Unangetastet: die public Naht `abstractions/session_tokens.py`, der Fake, die
Infrastruktur (`PostgresSessionTokens`), die HTTP-Antwort und sämtliche Specs.

## Warum die alte Form falsch war

**Die Orchestrierung war zerrissen.** Die Rollentabelle in
[`.rules/python/python-feature-slices.md`](../../.rules/python/python-feature-slices.md) weist dem
Handler die Orchestrierung zu — er allein. „Erst den Nutzer aufnehmen, dann die Sitzung ausstellen"
ist genau das, stand aber als eigener Schritt um den Handler herum. Zwei Stellen orchestrierten.

**Der Adapter fehlte.** Jede andere Naht hat einen: `UserRegistryAdapter`, `PasswordHasherAdapter`,
`IdnEncoderAdapter`, `EventPublisherAdapter`. Die Sitzung hatte keinen, also übersetzte der Schritt
selbst — `str(user.id)` und `user.registered_at.unix_seconds` standen mitten im Fachablauf. Das ist
die Arbeit, die die Rollentabelle dem Port-Adapter zuweist, und nur ihm.

**Ein Naht-Typ lief nach innen.** `Registration` hielt `IssuedSession` — ein Typ aus
`abstractions/`, also reine Primitive der Außengrenze. Das interne Ergebnis des Use Case war damit
aus einem Außengrenzen-Typ gebaut. Die Regel „kein DTO kreuzt die Grenze zum Handler" gilt in beide
Richtungen.

Nicht falsch war das **Verhalten**. Es bleibt unverändert.

## Warum kein Fehlerkanal am Port

`SessionIssuer.issue` gibt `Session` zurück, kein `Result`. Es gibt keinen *erwarteten* Fehlschlag.
Eine tote Datenbank ist ein Betriebsfall, keine Fachentscheidung — sie fällt als Exception bis zur
Middleware durch, so wie `PasswordHasher` es aus demselben Grund hält.

Ein halb ausgestellter Zustand kann dabei nicht entstehen. Nutzer-Zeile, Refresh-Token und
Outbox-Ereignis hängen in **derselben** Transaktion ([`src/api/composition.py`](../../src/api/composition.py),
`request_transaction`): eine Transaktion je Anfrage, `commit` am Ende, bei einer Exception wird nie
committet. Bricht die Ausstellung ab, wird nichts geschrieben — auch der Nutzer nicht. Kein Konto
ohne Token, kein Token ohne Konto.

## Was verworfen wurde

**Ein eigener Use Case für die Ausstellung.** Sie hat keinen eigenen Request und keine eigene
Außengrenze. „Registrieren erzeugt Nutzer **und** Sitzung" ist ein Vorgang.

**Ereignis plus eigener Slice, der die Sitzung nachträglich schreibt.** Der Vertrag verbietet es:
`POST /register` gibt Access- und Refresh-Token **in der Antwort** zurück (BACKEND.md Abschnitt 1).
Ein Ereignis ist asynchron; die Antwort kann nicht auf etwas warten, das später passiert. Zudem
wäre die Atomarität dahin — der Nutzer wäre committet, der Client hätte ein `201` ohne Token und
könnte es nie nachholen.

## Zur Aggregat-Frage

Ein Port ist kein Aggregat. `User` ruft niemanden; der Handler ruft zwei Ports. Das ist bei
`UserRegistry` heute schon so.

Die Sitzung **gehört** zu einem Nutzer — der Fremdschlüssel `fk_refresh_tokens_user_id` mit
`ondelete=CASCADE` erzwingt es. Sie ist aber nicht **Teil** des `User`-Aggregats: eigener
Lebenszyklus (ausstellen, rotieren, widerrufen, ablaufen), kein gemeinsamer Invariant, und einen
Nutzer zu laden hieße sonst, alle seine Tokens mitzuladen. Sie verweist über die Nutzer-Id auf ihn,
so wie BACKEND.md Abschnitt 1 es für `RefreshToken` bereits festlegt: ein **eigenes Aggregat**.

Die Glossar-Zeile in [`CONTEXT.md`](../../CONTEXT.md) sagte dazu „gehört keinem Aggregat" und war
damit irreführend. Sie ist nachgezogen.

## Nebenbefund — inzwischen aufgelöst

Die Geltungsdauern standen zum Zeitpunkt dieser Entscheidung als Konstanten in der Infrastruktur,
je einmal in der Ablage und im Signierer. Sie sind es nicht mehr:
[Die Geltungsdauern sind Konfiguration](2026-08-27-1930-geltungsdauern-sind-konfiguration-nicht-domaene.md)
holt sie in `TokenSettings` und lässt sie als `TokenLifetime` durch den Fachablauf laufen.
