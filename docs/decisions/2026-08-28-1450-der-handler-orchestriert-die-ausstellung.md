# Der Handler orchestriert die Ausstellung — die Wurzel gibt nur ihre Identität her

## Was entschieden wurde

`User.issue_credentials` und `CredentialIssuance` sind **gelöscht**. Der Handler führt die
Ausstellung wieder selbst, fasst dabei aber nur noch `user.id` an. Beide Mitspieler stellen ihre
Hälfte selbst aus; der Handler legt ab und paart.

```python
# jetzt, RegisterUserHandler._with_credentials
issued_at = self._clock.now()
issuance = RefreshToken.issue(
    user_id=user.id, secrets=self._secrets, issued_at=issued_at, lifetime=self._lifetimes.refresh
)
await self._refresh_tokens.store(issuance.refresh_token)
return Registration(
    user,
    IssuedCredentials.hydrate(
        self._access_tokens.sign(user.id, issued_at, self._lifetimes.access), issuance.grant
    ),
)
```

Fünf Änderungen tragen das:

1. **Der Handler orchestriert.** `User` baut kein fremdes Aggregat mehr und koordiniert keine
   Ports. Verknüpft werden Nutzer und Token ausschließlich über die → Nutzer-Id.
2. **`issued_at` kommt aus der Uhr, nicht aus `registered_at`.** Der Handler bekommt den
   `TimeProvider`, den die Fabrik schon hat, und liest **einmal** für beide Token.
3. **`AccessTokens.sign` gibt eine `Grant` zurück, keinen `str`.** Wer signiert, kennt die Dauer
   bereits — er paart selbst, statt den Aufrufer paaren zu lassen.
4. **`RefreshTokens` erbt nicht mehr von `TokenSecrets`.** Zwei getrennte Ports, zwei Adapter
   (`TokenSecretsAdapter`, `RefreshTokensAdapter`) über derselben Naht.
5. **`TokenLifetimes` ist ein Wert.** Die beiden Dauern reisen nicht mehr als zwei gleichnamige
   Parameter durch Fabrik, Handler und Ausstellung.

Dazu: `IssuedCredentials` bekommt die `ConstructionKey`-Sperre, die `Grant` und
`RefreshTokenIssuance` schon tragen, und `IssuedCredentials.fold` reicht seine vier Werte über den
Callback-Typ `CredentialsPresenter` **keyword-only** heraus.

Unangetastet: die HTTP-Antwort, die public Naht, `PostgresSessionTokens`, `JwtAccessTokens`,
sämtliche Specs, das Datenbankschema — keine Migration.

## Warum die Wurzel es nicht mehr tut

[1045](2026-08-28-1045-die-wurzel-stellt-ihre-zugangsdaten-aus.md) verschob den Ablauf in `User`,
weil der Handler sich `user.id` und `user.registered_at` herausnahm — Feature Envy. Der Umzug hat
den Envy geheilt und dafür etwas Schlimmeres eingehandelt: die Wurzel hielt zwei Ports, baute ein
**fremdes** Aggregat (`RefreshToken`) und gab es heraus, während sie selbst nur zwei eigene Felder
beisteuerte. Das ist keine Aggregat-Operation, sondern ein Fachablauf — und ein Fachablauf über
zwei Aggregate gehört dem Use Case, nicht einem der beiden Aggregate
([`anti-anemic-domain.md`](../../.rules/common/anti-anemic-domain.md)).

Der Envy verschwindet trotzdem, denn der Grund für ihn war nicht der Ort, sondern die **Zahl der
Griffe**. Bleibt genau einer — die Identität —, ist es kein Herausnehmen mehr, sondern das, was
eine Id ist: der Verweis, über den zwei Aggregate sich kennen.

## Warum die Uhr und nicht `registered_at`

`registered_at` ist der Zeitpunkt der Aufnahme, nicht der Zeitpunkt einer Ausstellung. Dass beide
bei der Registrierung zusammenfallen, ist Zufall dieses einen Use Case: der Anmelde-Pfad (#53)
stellt dieselben Token aus und hat kein `registered_at`. Die Uhr trägt beide Fälle, das Feld nur
einen.

Die Zusage aus [0930](2026-08-28-0930-das-aggregat-zieht-sein-geheimnis-selbst.md) — „dieselbe
Ablesung für alles, was zusammen entsteht" — bleibt dort erhalten, wo sie zählt: **eine** Ablesung
im Handler für beide Token. Nur die Kopplung an die Nutzer-Zeile fällt.

## Warum `Grant.token` ein `str` bleibt

[0807](2026-08-28-0807-das-aggregat-stellt-sich-selbst-aus.md) begründete das mit „die Grenze
verläuft bei *ist ein Feld der Domäne*". Seit `Grant` in der Domäne steht, trägt diese Begründung
nicht mehr. Die neue ist enger: ein Value Object rechtfertigt sich durch eine **Regel**, die es
hält. Ein signierter Access-Token und ein gezogenes Refresh-Geheimnis haben für die Domäne keine —
sie werden nie gelesen, nie verglichen, nie geprüft, nur weitergereicht. Was zu schützen war, ist
die *Paarung* mit der Geltungsdauer und die *Herkunft*; beides hält `Grant` selbst über seine
`ConstructionKey`-Sperre. Ein `TokenString`-Wrapper darüber wäre ein Typ ohne Invariante.

## Warum die Ports getrennt sind statt vererbt

`RefreshTokens(TokenSecrets, Protocol)` sparte eine Deklaration und kostete die Trennung: wer den
breiten Port hielt, hielt beide Fähigkeiten, und nur die Signatur von `RefreshToken.issue` hielt
das Aggregat von `store` fern. Ein `Protocol` ist strukturell — dieselbe Ablage erfüllt beide
Verträge ohne jede Vererbung, und jeder Aufrufer verlangt genau das, was er benutzt
([`python-dependencies.md`](../../.rules/python/python-dependencies.md), „Komposition über
`Protocol` statt Vererbung").

## Was das ersetzt

- [1045](2026-08-28-1045-die-wurzel-stellt-ihre-zugangsdaten-aus.md) ist in seinem Kern
  **zurückgenommen**: `User.issue_credentials` und `CredentialIssuance` gibt es nicht mehr. Was
  bleibt, ist der Ort von `Grant` und `IssuedCredentials` — die Domäne.
- [0930](2026-08-28-0930-das-aggregat-zieht-sein-geheimnis-selbst.md) gilt weiter, mit einer
  Ausnahme: die Bindung von `issued_at` an die Nutzer-Zeile ist aufgehoben.
- [1120](2026-08-28-1120-die-zugangsdaten-geben-heraus-was-sie-wissen.md) gilt weiter; der
  Callback-Typ ist jetzt benannt statt positional.
