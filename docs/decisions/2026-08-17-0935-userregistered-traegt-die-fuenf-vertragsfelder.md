# `UserRegistered` traegt die fuenf im Ticket genannten Felder — auch `email`

**Datum:** 2026-08-17, 09:35
**Anlass:** Contract-Test aus Stufe 2 von Ticket
[#51](https://github.com/mbalzert1978/fit_back/issues/51).

## Was entschieden wurde

Die Nutzlast von `UserRegistered` traegt ab sofort fuenf Felder, in camelCase:

```json
{ "userId": "…", "email": "…", "locale": "de", "timeZoneId": "Europe/Berlin", "registeredAt": 1798221600 }
```

Vorher trug die Nutzlast `user_id` und `locale`.

> **Nachtrag vom selben Tag, nach dem Review zu PR #91.** Dieser Eintrag hielt hier
> urspruenglich fest, der veroeffentlichte Vertrag liege als Beispiel-Datei unter
> `contracts/events/user_registered/examples/` und werde von einem eigenen Contract-Spec
> dagegen gemessen. **Dieser Mechanismus ist zurueckgenommen** — Contract-Testing laeuft in
> diesem Repo ueber Pact, consumer-driven vom Frontend nach unten
> ([#94](https://github.com/mbalzert1978/fit_back/issues/94)). Die Entscheidung *dieses*
> Eintrags — welche fuenf Felder die Nutzlast traegt — ist davon unberuehrt und gilt
> unveraendert; gedeckt ist sie heute durch die Slice-Specs. Nur die Begruendung ueber die
> Beispiel-Datei ist entfallen. Der Absatz ist stehen gelassen und nicht umgeschrieben, weil
> dieses Verzeichnis ein datiertes Protokoll ist und kein gepflegter Ist-Stand.

## Warum, und wogegen abgewogen wurde

Das Ticket nennt die Felder namentlich („mindestens `userId`, `email`, `locale`, `timeZoneId`,
`registeredAt`") — ein pruefbares Abnahmekriterium. Es sagt im selben Atemzug aber auch: „Ein Feld,
das kein Konsument liest, gehoert nicht in die Payload." Beides zusammen geht bei **`email`** nicht
auf:

- `userId` — Goals und Diary brauchen die Identitaet. Unstrittig.
- `locale` — Diary benennt seine Standard-Mahlzeiten-Slots danach (`docs/milestones/m4-diary.md`).
- `timeZoneId` — die Zeitzone entscheidet, welcher Kalendertag ein Zeitpunkt fuer diesen Nutzer
  ist; ohne sie kann Diary keinen Tag bilden.
- `registeredAt` — der fachliche Zeitpunkt, damit die Nutzlast fuer sich lesbar ist und ein
  Konsument nicht in den Transport-Umschlag greifen muss.
- **`email`** — kein bekannter Konsument liest sie. `docs/Draft/BACKEND.md`, `m2-goals.md` und
  `m4-diary.md` nennen keinen. Der Docstring von `contracts/user_registered.py` argumentierte
  bislang ausdruecklich dagegen („E-Mail und Anzeigename bleiben im Identity-Context; was hier
  steht, ist ausserhalb nicht mehr einzufangen").

**Entschieden wurde fuer die namentliche Aufzaehlung**, weil sie das explizite, pruefbare Kriterium
des Tickets ist und weil das Ticket den Konflikt selbst vorwegnimmt: „Bei Abweichung ist die
Beispiel-Datei massgeblich, nicht der Produktionscode" — es rechnet also damit, dass der Code der
Liste nachzieht, nicht umgekehrt.

**Der Gegeneinwand bleibt offen und ist bewusst hier festgehalten**, weil er nicht schwaecher wird,
nur weil er unterlag: `email` ist personenbezogen, verlaesst mit diesem Feld den Context, der sie
haelt, und laesst sich danach nicht wieder einfangen. Das Ticket erklaert das Entfernen eines
Feldes selbst zum Bruch, der ein eigenes Ticket mit Konsumenten-Nachzug braucht. Solange **kein**
Konsument existiert (Goals kommt mit M2, Diary mit M4), ist die Ruecknahme noch billig — danach
nicht mehr. Wer diese Entscheidung revidieren will, tut es am besten **vor** M2.

## Nebenentscheidungen

- **camelCase statt snake_case** in der Nutzlast. Die Beispiel-Datei *ist* das Wire-Format, das
  Ticket benennt die Felder in camelCase, und das uebrige veroeffentlichte JSON dieses Repos (der
  HTTP-Rand) ist ebenfalls camelCase.
- **`registeredAt` als Unix-Sekunden**, nicht als ISO-8601. So haelt es dieses Repo ueberall ausser
  am HTTP-Rand ([`2026-08-06-1340`](./2026-08-06-1340-unix-epoch-statt-datetime.md)); die
  Outbox-Spalte `occurred_at` fuehrt denselben Zeitpunkt in derselben Einheit.
- **Der Zeitpunkt steht in Umschlag und Nutzlast.** Der Umschlag braucht ihn fuer Zustellung und
  Reihenfolge, die Nutzlast ist der Vertrag und soll fuer sich lesbar sein.
- **Ein Beispiel, nicht mehrere.** `UserRegistered` kennt genau einen Fall. Ein zweites Beispiel
  mit derselben Feldmenge machte die Zusage „entspricht **genau einem** Beispiel" unerfuellbar;
  ein zweites mit anderer Feldmenge gehoert zu einer erhoehten `<version>`.
