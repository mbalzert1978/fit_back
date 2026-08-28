# Das Aggregat zieht sein Geheimnis selbst — der Ablauf zieht in den Handler

## Was entschieden wurde

Drei Dinge auf einmal, weil sie dieselbe Ursache hatten:

1. **`RefreshToken.issue` bekommt die Geheimnis-Quelle als Parameter** und zieht sein Geheimnis
   selbst. Method Injection in eine Aggregat-Methode — die Abhängigkeit geht in die **Methode**,
   nie in ein Feld.
2. **Der Ablauf steht im Handler.** `SessionIssuer` und `SessionIssuerAdapter` sind gelöscht. An
   ihrer Stelle stehen drei schmale Domain-Ports und zwei Adapter, die nur noch übersetzen.
3. **`IssuedCredentials` verlässt die Domäne** und zerfällt in zwei `Grant` — je ein Token mit
   seiner Geltungsdauer.

| neu | was es ist |
|-----|------------|
| `domain/ports/token_secrets.py` | `TokenSecrets` — `mint() -> TokenSecret`, die eine Operation, die das Aggregat braucht |
| `domain/ports/refresh_tokens.py` | `RefreshTokens(TokenSecrets)` — dazu `store(token: RefreshToken)` |
| `domain/ports/access_tokens.py` | `AccessTokens` — `sign(user_id, issued_at, lifetime) -> str` |
| `application/register_user/credentials.py` | `Grant` und `IssuedCredentials` |
| `adapters/refresh_tokens_adapter.py` | faltet Naht↔Domäne, kein Ablauf |
| `adapters/access_tokens_adapter.py` | faltet Naht↔Domäne, kein Ablauf |

Gelöscht: `domain/ports/session_issuer.py`, `domain/value_objects/issued_credentials.py`,
`adapters/session_issuer_adapter.py`.

Unangetastet: die HTTP-Antwort, die public Naht (`MintedSecret`, `RefreshTokenRecord`,
`RegisterUserSessionTokens`, `RegisterUserAccessTokens`), der Fake, `PostgresSessionTokens`,
`JwtAccessTokens`, sämtliche Specs, das Datenbankschema — **keine Migration**.

## Warum die alte Form falsch war

**Der Adapter war der Orchestrator.** `SessionIssuerAdapter.issue` rief vier Naht-Operationen in
fester Reihenfolge: Geheimnis ziehen, Aggregat bauen, ablegen, signieren. Das ist ein Fachablauf,
kein Übersetzen. [Die Sitzung entsteht im Handler](2026-08-27-1630-die-sitzung-entsteht-im-handler.md)
behauptete, der Ablauf stehe im Handler — dort stand eine Zeile, und der Ablauf lag eine Schicht
tiefer hinter einem Port. Der Titel jener Entscheidung stimmt jetzt.

[Der Refresh-Token ist ein Aggregat](2026-08-27-1830-refresh-token-ist-ein-aggregat.md)
verteidigte das mit „die Übersetzung **einer** fachlichen Handlung". Die Verteidigung trägt nicht:
eine Übersetzung ruft einen Mitspieler, ein Ablauf ruft mehrere in einer Reihenfolge, die man
begründen muss. Hier waren es zwei Mitspieler und vier Aufrufe.

**Das Aggregat bekam sein Geheimnis gereicht.** Auch nach
[0807](2026-08-28-0807-das-aggregat-stellt-sich-selbst-aus.md) zog es der Adapter und legte es dem
Aggregat hin. Damit lag „ein Refresh-Token entsteht nicht ohne frisches Geheimnis" außerhalb des
Aggregats. Jetzt liegt es drin: ohne `TokenSecrets` kommt niemand an `issue` vorbei, und niemand
sieht das Geheimnis vor dem Aggregat.

Dass das ginge, war in 0807 falsch bestritten („das Aggregat kann keinen Zufall ziehen"). Es kann
den Zufall nicht *erzeugen* — davon abhängen kann es sehr wohl. Genau dafür gibt es
Method Injection.

**`IssuedCredentials` hielt vier lose Primitive.** Zwei Token und zwei Dauern nebeneinander, und
nichts hielt das eine Paar vom anderen fern. Jetzt sind es zwei `Grant`, und jedes ist für sich
vollständig.

## Warum `TokenSecrets` und `RefreshTokens` zwei Protokolle sind

Es ist **ein** Mitspieler — in der Produktion `PostgresSessionTokens`, in Specs
`InMemorySessionTokens` —, deshalb erbt `RefreshTokens` von `TokenSecrets` und der Handler hält
genau eine Abhängigkeit. Gelesen wird trotzdem getrennt: `RefreshToken.issue` verlangt nur
`TokenSecrets` und bekommt damit kein `store` in die Hand. Ein Aggregat, das sich selbst ablegen
kann, ist ein Active Record.

Das ist Interface Segregation an der Stelle, an der sie etwas verhindert, ohne einen zweiten
Mitspieler zu erfinden, den es nicht gibt.

## Was `IssuedCredentials` aus der Domäne befreit hat

In [0807](2026-08-28-0807-das-aggregat-stellt-sich-selbst-aus.md) stand, der Typ *müsse* in der
Domäne bleiben, weil der Domain-Port `SessionIssuer` ihn zurückgibt und ein Domain-Port nichts aus
der Application-Schicht sprechen darf. Das war richtig — und übersah, dass der Port selbst zur
Debatte stand. Mit `SessionIssuer` fällt der Zwang.

Die neuen Ports sprechen durchgehend Domänentypen: `TokenSecret`, `RefreshToken`, `UserId`,
`Timestamp`, `TokenLifetime`. `AccessTokens.sign` gibt einen `str` zurück, und das bleibt so: der
signierte Token trägt keine Regel, wird nie wiedergelesen und ist für die Domäne undurchsichtig.
Gepaart wird er sofort — mit seiner Geltungsdauer, im `Grant` des Slice.

## Was der Handler dafür bezahlt

Er wächst von sechs auf sieben Abhängigkeiten und `_with_credentials` von vier auf drei plus eine
ausgelagerte Hilfsmethode. Das ist der bewusste Preis: der Ablauf ist jetzt dort lesbar, wo der Use
Case steht, statt hinter einem Port zu verschwinden, der „ein Schritt" hieß und vier war.

Der Zufall taucht im Handler **nicht** auf. Er steht in keiner seiner Zeilen — `RefreshToken.issue`
zieht ihn, und der Handler reicht nur die Quelle weiter. Genau das war der Einwand von
[1830](2026-08-27-1830-refresh-token-ist-ein-aggregat.md) gegen mehrere Ports im Handler („dann
kennte der Fachablauf die Reihenfolge von Zufall, Ablage und Signatur"). Er ist damit erledigt,
nicht überstimmt: der Handler kennt Ablage und Signatur, den Zufall kennt das Aggregat.
