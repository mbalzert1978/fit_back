# Die Geltungsdauern sind Konfiguration, keine Domäne

## Was entschieden wurde

Die beiden Zahlen — 15 Minuten Access-Token, 60 Tage Refresh-Token — sind eine **Einstellung des
Prozesses** und keine Konstante der Domäne. Sie kommen als typisierte Konfiguration herein, den
Weg, den jede andere Naht dieses Slice auch geht.

| neu | was es ist |
|-----|------------|
| `application/register_user/abstractions/token_options.py` | `RegisterUserTokenOptions` — der Vertrag, zwei Sekundenwerte |
| `adapters/test_api/fakes/token_options.py` | `FixedTokenOptions` — der Fake für Specs |
| `src/settings.py`, `TokenSettings` | die Sektion, gelesen aus `ACCESS_TOKEN_SECONDS` und `REFRESH_TOKEN_SECONDS` |

Gelöscht: `domain/token_lifetimes.py` mit den beiden Konstanten. Damit ist der Abschnitt „Die
Lebensdauern standen dreimal da" aus
[Das Aggregat `RefreshToken`](2026-08-27-1830-refresh-token-ist-ein-aggregat.md) überholt: sie
stehen weiterhin **einmal**, nur nicht mehr in der Domäne.

## Wer prüft, und warum nicht die Domäne

**Geprüft wird in `TokenSettings` und sonst nirgends.** Die Grenzen stehen dort als
`Field(gt=0, le=…)`, gegen dieselbe Konstante, die auch die Vorgabe ist — eine Zahl, nicht zwei, so
kann keine Vorgabe außerhalb ihrer eigenen Grenze liegen.

Der Lackmustest ist die Frage, ob es eine **Geschäftsinvariante** ist. Sie ist es nicht:

- Der Wert erreicht die Domäne nie über eine ihrer Operationen. Er wird beim Zusammenbau einmal
  hineingereicht; kein Aggregat, kein Nutzer und kein Fachablauf kann ihn ändern.
- Der Fehlerfall ist eine **Fehlbedienung des Prozesses**, kein fachlicher Ausgang. Es gibt keine
  Registrierung, die daran „erwartet scheitert".

Eine Prüfung in der Domäne hätte diesen Unterschied verwischt — und sie hätte zu spät gegriffen:
`TokenSettings` wird im Lifespan gelesen (`src/main.py`), ein unbrauchbarer Wert stoppt damit den
**Start**. Läge die Prüfung im Value Object, käme sie erst bei der ersten Anfrage — derselbe
Betriebsregress, den `JWT_SECRET` gerade nicht hat.

Was die Domäne behält, gehört ihr: **dass** ein Token eine Geltungsdauer hat (`TokenLifetime`) und
**wann** er damit abläuft (`expires_from`). `TokenLifetime.hydrate` nimmt die geprüfte Zahl an, wie
jede andere Rekonstruktion aus vertrauenswürdiger Quelle.

## Warum das eine Exception ist und kein `Result`

Eine unbrauchbare Geltungsdauer ist ein falsch gesetzter Prozess, kein fachlicher Ausgang. Also
fliegt ein `ValidationError` bis `get_settings` und von dort als `RuntimeError` weiter — dieselbe
Behandlung wie bei jedem anderen Konfigurationsfehler. Sie zieht keinen Fehlercode und keine
i18n-Vorlage nach sich, weil sie nie einen Nutzer erreicht.

## Warum der Handler die Konfiguration hält und nicht der Adapter

`RegisterUserTokenOptions` ist **kein Domain-Port**. Ein Port benennt einen Mitspieler, auf dem
etwas aufgerufen wird; hier wird nichts aufgerufen, hier werden zwei Zahlen gelesen. Deshalb liegt
der Vertrag bei den übrigen Nähten des Slice und trägt wie sie nur Primitive — nicht unter
`domain/ports/`.

Der Handler liest sie und reicht sie weiter. Das hält den Weg sichtbar: wer den Fachablauf liest,
sieht, mit welcher Geltungsdauer ausgestellt wird. Läge sie im Adapter, wäre sie eine stille
Eigenschaft der Verdrahtung.

Die Umwandlung Primitiv → `TokenLifetime` passiert **einmal**, in der Fabrik (`pipeline.py`), an
der äußeren Naht. Ab dort spricht der Fachablauf durchgehend Domänentypen — auch `SessionIssuer`
und `IssuedCredentials`; ein Domain-Port mit `int`-Parametern wäre die Ausnahme, die die Regel
„die Domäne spricht nur VOs/Entitäten" nicht verträgt.
