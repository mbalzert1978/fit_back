# Die Obergrenze der Geltungsdauer steht in der Domäne

## Was entschieden wurde

Es gibt wieder ein Value Object: `domain/value_objects/token_lifetime.py` mit `TokenLifetime`.
Es trägt **beide** Grenzen und die eine Ablauf-Rechnung.

| was | wo |
|-----|-----|
| Untergrenze (`> 0`) | `TokenLifetime._within` |
| Obergrenze `ACCESS_TOKEN_MAXIMUM_SECONDS = 900` | `token_lifetime.py` |
| Obergrenze `REFRESH_TOKEN_MAXIMUM_SECONDS = 5_184_000` | `token_lifetime.py` |
| Ablauf = `issued_at + seconds` | `TokenLifetime.expires_from` |

`SessionIssuer.issue` und `RefreshToken.issue` nehmen ab jetzt `TokenLifetime` statt `int`.
Umgewandelt wird in der Fabrik `build_register_user_pipeline` — sie ist die eine Stelle, an der der
Slice zusammengesteckt wird (`.rules/python/python-factories.md`), und damit die Naht, an der
Primitive enden. Der Handler bekommt zwei `TokenLifetime` gereicht und spricht nur noch Domäne.

`TokenSettings` in `src/settings.py` prüft nichts mehr (`gt=0` ist entfallen).

## Warum die Obergrenze nötig war

`BACKEND.md` Abschnitt 0, Punkt 8 sagt zu: Access-Token 15 Minuten, Refresh-Token 60 Tage. Nach
[Die Geltungsdauern sind Konfiguration](2026-08-27-1930-geltungsdauern-sind-konfiguration-nicht-domaene.md)
konnte `REFRESH_TOKEN_LIFETIME=99999999` diese Zusage **still** brechen: die Konfiguration prüfte
nur, dass die Zahl positiv ist. Eine Zusage, die eine Umgebungsvariable ohne Widerspruch aufheben
kann, ist keine.

Die Zusage ist die Grenze. Die Umgebung darf die Dauer **verkürzen**, nie verlängern. Damit bleibt
die Aussage aus 1930 richtig — *welcher* Wert gilt, entscheidet die Umgebung —, und die Domäne
entscheidet weiterhin nur, was zulässig ist.

## Was das an 1930 zurücknimmt

Zwei Sätze jener Entscheidung gelten nicht mehr:

- „`TokenLifetimes` als Value Object … wurde zwischenzeitlich gebaut und wieder verworfen." Das
  Value Object ist zurück — aber mit einem Inhalt, den es damals nicht hatte: einer Obergrenze und
  der Ablauf-Rechnung. Der damalige Einwand („der Gewinn wäre keiner gewesen") traf einen bloßen
  Behälter, nicht diesen.
- „`SessionIssuer` nimmt die beiden Zahlen als Primitive entgegen — das ist die Ausnahme, die die
  Regel … verträgt." Die Ausnahme fällt. `.rules/python/python-feature-slices.md` („Die Domäne
  spricht nur VOs/Entitäten") gilt ohne sie; der Nachbar-Port `PasswordHasher` hielt sie ohnehin
  ein.

Alles andere aus 1930 bleibt: kein Domain-Port für die Konfiguration, der Handler hält sie, und ein
unbrauchbarer Wert ist eine `ValueError` und kein `Result`.

## Was das kostet

`TokenSettings` prüft nicht mehr beim Start, sondern `TokenLifetime` beim Bau des Handlers — und
der entsteht je Anfrage. Eine falsch gesetzte Umgebungsvariable fällt damit erst bei der ersten
Registrierung auf, dann aber laut (500 über die Middleware) statt still. Ein Startcheck würde
`src/settings.py` an die Identity-Domäne hängen; das ist der teurere Tausch. Kommt ein zweiter
Slice mit Token-Ausstellung dazu (#52), ist der Punkt neu zu bewerten.

## Was dabei mit erledigt ist

Die Ablauf-Rechnung stand zweimal: `RefreshToken.issue` rechnete sie in der Domäne, der
`SessionIssuerAdapter` rechnete sie für den Access-Token selbst. Jetzt rechnet sie `expires_from`,
für beide Token.
