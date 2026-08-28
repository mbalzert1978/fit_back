# Das Aggregat stellt sich selbst aus — der Klartext verlässt die Ausstellung nur gepaart

## Was entschieden wurde

`RefreshToken.issue` nimmt das Geheimnis als **Ganzes** entgegen und gibt Aggregat und Klartext als
**ein** Ergebnis zurück. Die Paarung „dieser Klartext gehört zu diesem Abdruck" entsteht damit in
der Domäne und nicht mehr im Adapter.

| neu | was es ist |
|-----|------------|
| `domain/value_objects/token_secret.py` | `TokenSecret` — Klartext und `TokenHash` als ein Wert, `hydrate(plaintext, hashed)` |
| `domain/entities/refresh_token.py` | `RefreshTokenIssuance` — das ausgestellte Aggregat samt seinem Klartext |

Geändert: `RefreshToken.issue(user_id, secret, issued_at, lifetime) -> RefreshTokenIssuance` statt
`(…, token_hash, …) -> RefreshToken`. Der Adapter `SessionIssuerAdapter` faltet die Naht-Primitive
über `_as_secret` nach innen und liest den Klartext aus der Ausstellung; `_as_record` nimmt jetzt
die Ausstellung statt des nackten Aggregats.

Unangetastet: die HTTP-Antwort, die Naht (`MintedSecret`, `RefreshTokenRecord`,
`RegisterUserSessionTokens`), der Fake, `PostgresSessionTokens`, das Datenbankschema — **keine
Migration**. `IssuedCredentials` behält seine vier Felder.

## Warum die alte Form falsch war

**Das Aggregat besaß seine eigene Geburt nicht.** `mint_secret()` gab beide Hälften an den Adapter;
der Adapter reichte die eine als `TokenHash` in `RefreshToken.issue` und die andere als Klartext in
`IssuedCredentials`. Die Regel, auf der die ganze Sicherheit ruht — *der ausgegebene Klartext ist
genau der, dessen Abdruck abgelegt wurde* — stand damit in der Application-Schicht, als Reihenfolge
von vier Zeilen. Sie war nirgends ein Typ, nichts hätte sie gehalten, und ein vertauschter
Ausdruck an dieser Stelle wäre kein Compilerfehler gewesen, sondern ein stiller Anmeldefehler in
Produktion.

`RefreshToken.issue` bekam einen fertigen Abdruck gereicht und musste glauben, dass er stimmt. Ein
Aggregat, dem man seine Invariante fertig hinlegt, hält keine.

**Jetzt gibt es keinen Weg mehr daran vorbei.** Wer den Klartext will, muss durch
`RefreshTokenIssuance` — und bekommt damit zwangsläufig das Aggregat, dessen Abdruck zu ihm passt.
Beide Typen tragen den Modul-Schlüssel aus `refresh_token.py`; von außen ist keine Paarung baubar
([Die Wurzel hält ihre Invarianten selbst](2026-08-26-2030-die-wurzel-haelt-ihre-invarianten-selbst.md)).

## Was das an der Entscheidung vom 27.08. korrigiert

[Der Refresh-Token ist ein Aggregat](2026-08-27-1830-refresh-token-ist-ein-aggregat.md) schloss:
„Der Klartext geht vom Aussteller direkt in die `IssuedCredentials` … Er kommt in der Domäne
**nicht** vor: `RefreshToken.issue` bekommt nur den `TokenHash`."

Diese Hälfte ist zurückgenommen. Der Klartext **reist** jetzt durch die Domäne — als Parameter
hinein, als Rückgabe hinaus. Das Ziel jener Formulierung bleibt trotzdem erfüllt, und zwar an der
Stelle, an der es zählt: der Klartext ist **kein Feld** von `RefreshToken` und steht nicht in
`RefreshTokenRecord`. Es gibt weiterhin keinen Weg, auf dem er in eine abgelegte Zeile geriete.

Der damalige Satz verwechselte „darf nicht abgelegt werden" mit „darf nicht vorkommen". Der
zweite, schärfere Verzicht kostete die Aggregat-Hoheit und kaufte dafür nichts.

## Warum `IssuedCredentials` trotzdem im `domain/` bleibt

Der naheliegende Folgeschritt — `IssuedCredentials` als reines Ausgabe-DTO in den Slice
verschieben — wurde geprüft und **verworfen**. Er scheitert an zwei bestehenden Regeln, und zwar
gleichzeitig:

- `SessionIssuer` ist ein **Domain-Port** (`domain/ports/`). Gäbe er einen Application-Typ zurück,
  zeigte die Domäne nach außen; der `context-layers`-Contract in `setup.cfg` verbietet das
  maschinell.
- Den Port stattdessen nach `application/register_user/abstractions/` zu ziehen, geht auch nicht:
  über diese Naht wandern **ausschließlich Primitive**
  ([`python-feature-slices.md`](../../.rules/python/python-feature-slices.md)), `SessionIssuer`
  aber nimmt `User` und `TokenLifetime` und ist damit ein ACL nach innen, keine Naht nach außen.

`IssuedCredentials` ist also zu Recht ein Domänen-Value-Object: es ist das Ergebnis der
Domänen-Operation „stelle diesem Nutzer Zugangsdaten aus", und die Geltungsdauern reisen mit, weil
die Domäne den Ablauf entscheidet. Dass seine vier Felder eins zu eins in die HTTP-Antwort gehen,
macht es nicht zum Transport-Typ — es macht die Antwort zu einer schmalen Projektion darauf.

## Warum die zwei Token weiter rohe `str` sind

`access_token` und `refresh_token` bekommen **kein** eigenes Value Object, obwohl der Abdruck eines
hat. Die Grenze verläuft nicht bei „ist geheim", sondern bei „ist ein Feld der Domäne":

- `TokenHash` ist eine **Spalte** des Aggregats. Er wird abgelegt, wiedergelesen und verglichen —
  ein Typ, der über seine Lebensdauer Bestand hat.
- Klartext und Access-Token sind Werte **auf dem Weg nach draußen**. Sie tragen keine Regel, werden
  nie wiedergelesen und existieren genau einen Request lang.

Ein VO ohne Regel und ohne zweiten Leser wäre eine Lazy Class — genau das, was
`verifier-lazy-class` und `verifier-speculative-generality` in diesem Repo abweisen. Der Schutz, um
den es hier geht, sitzt ohnehin nicht am Typ, sondern an `repr=False` und an der Paarung durch
`RefreshTokenIssuance`.
