# Die Geltungsdauern sind Konfiguration, keine Domäne

## Was entschieden wurde

Die beiden Zahlen — 15 Minuten Access-Token, 60 Tage Refresh-Token — sind eine **Einstellung des
Prozesses** und keine Konstante der Domäne. Sie kommen als typisierte Konfiguration herein, den
Weg, den jede andere Naht dieses Slice auch geht.

| neu | was es ist |
|-----|------------|
| `application/register_user/abstractions/token_options.py` | `RegisterUserTokenOptions` — der Vertrag, zwei Sekundenwerte |
| `adapters/test_api/fakes/token_options.py` | `FixedTokenOptions` — der Fake für Specs |
| `src/settings.py`, `TokenSettings` | die Sektion, gelesen aus `ACCESS_TOKEN_LIFETIME` und `REFRESH_TOKEN_LIFETIME` |

Gelöscht: `domain/token_lifetimes.py` mit `ACCESS_TOKEN_LIFETIME` und `REFRESH_TOKEN_LIFETIME`.
Damit ist der Abschnitt „Die Lebensdauern standen dreimal da" aus
[Das Aggregat `RefreshToken`](2026-08-27-1830-refresh-token-ist-ein-aggregat.md) überholt: sie
stehen weiterhin **einmal**, nur nicht mehr in der Domäne.

Der Weg der beiden Zahlen ist damit: `TokenSettings` → Composition Root → Fabrik → **Handler** →
`SessionIssuer.issue(user, access_token_seconds, refresh_token_seconds)` → Adapter →
`RefreshToken.issue(..., lifetime_seconds)`.

## Warum die Konstante in der Domäne falsch war

Eine Konstante sagt: dieser Wert folgt aus der Fachlichkeit und ist überall derselbe. Für eine
Geltungsdauer stimmt das nicht. Sie unterscheidet sich zwischen Entwicklung, Test und Produktion,
und wer sie ändern will, will dafür nicht die Domäne anfassen.

Die Domäne behält, was ihr gehört: **dass** ein Token eine Geltungsdauer hat und **dass** diese
positiv sein muss. `RefreshToken.issue` weist eine Dauer von null oder weniger ab — ein Token, der
im selben Augenblick abläuft, in dem er entsteht, ist keiner.

## Warum das eine Exception ist und kein `Result`

Eine unbrauchbare Geltungsdauer ist ein falsch gesetzter Prozess, kein fachlicher Ausgang. Es gibt
keine Registrierung, die daran „erwartet scheitert". Also fliegt eine `ValueError` bis zur
Middleware durch, wie bei `PasswordHasher` und aus demselben Grund
(`.rules/python/python-error-handling.md`). Sie zieht keinen Fehlercode und keine i18n-Vorlage nach
sich, weil sie nie einen Nutzer erreicht.

## Warum der Handler die Konfiguration hält und nicht der Adapter

`RegisterUserTokenOptions` ist **kein Domain-Port**. Ein Port benennt einen Mitspieler, auf dem
etwas aufgerufen wird; hier wird nichts aufgerufen, hier werden zwei Zahlen gelesen. Deshalb liegt
der Vertrag bei den übrigen Nähten des Slice und trägt wie sie nur Primitive — nicht unter
`domain/ports/`.

Der Handler liest sie und reicht sie weiter. Das hält den Weg sichtbar: wer den Fachablauf liest,
sieht, mit welcher Geltungsdauer ausgestellt wird. Läge sie im Adapter, wäre sie eine stille
Eigenschaft der Verdrahtung.

Der Adapter bleibt dadurch so schmal wie zuvor, und `SessionIssuer` nimmt die beiden Zahlen als
Primitive entgegen — das ist die Ausnahme, die die Regel „ein Domain-Port spricht Domänentypen"
verträgt: es sind Sekunden, kein Fachbegriff, der ein Value Object verdient hätte.

## Was ersetzt wird

`TokenLifetimes` als Value Object in `domain/value_objects/` wurde zwischenzeitlich gebaut und
wieder verworfen. Ein Value Object hätte die Zahlen erneut zu einem Gegenstand der Domäne gemacht,
nur mit mehr Zeremonie: `ConstructionKey`, `hydrate`, ein Eintrag im Glossar. Der Gewinn wäre
keiner gewesen — geprüft wird der Wert ohnehin dort, wo er gebraucht wird.
