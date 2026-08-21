# Die Provider-Verifikation trägt englische Bezeichner

**Entschieden am 2026-08-21, 21:15.** Nachfolger von
[`2026-08-21-1420-mechanik-der-provider-verifikation.md`](./2026-08-21-1420-mechanik-der-provider-verifikation.md).
**Jenes Dokument bleibt gültig in allem, was es über die Mechanik sagt** — die Verifikation als
gewöhnlicher pytest-Test, die in-process laufenden Provider-States, der Ausschluss über den Pfad,
der Mechanik-Pact als grüner Gegenbeweis, die beiden Fallstricke rund um asyncpg und den
Startup-Abbruch. **Überholt sind dort ausschließlich die Namen**, mit denen der Code diese Mechanik
schreibt. Der eingeklebte pytest-Auszug im Vorgänger bleibt wörtlich so stehen, wie er gelaufen
ist; er ist ein Beleg und wird nicht nachträglich umgeschrieben.

## Was entschieden wurde

**Code, Bezeichner, Kommentare und Docstrings sind Englisch** — auch dort, wo das Repo sonst
durchgehend deutsch dokumentiert. Die Regel steht im Abschnitt „Sprache der Dokumentation" der
[`CLAUDE.md`](../../CLAUDE.md) und nimmt Code ausdrücklich von der Deutsch-Pflicht aus; die
Contract-Tests waren die letzte Stelle, an der sie noch nicht durchgezogen war. Die Dokumentation
selbst — dieses Dokument eingeschlossen — bleibt Deutsch.

**Ausgenommen bleiben die Provider-State-Texte.** `NO_ACCOUNT` und `ACCOUNT_EXISTS` heißen
englisch, ihr *Inhalt* aber (`"Keine Registrierung mit a@b.de vorhanden"`, `"Nutzer a@b.de existiert
mit Passwort geheim123"`) bleibt Wort für Wort deutsch: Pact matcht diese Strings exakt gegen die
Vertragsdatei des Consumers. Wer sie übersetzt, findet den State nicht mehr. Dasselbe gilt für die
Interaktions-Beschreibungen, die in der Ausgabe auftauchen — die stammen aus dem Pact, nicht aus
unserem Code.

## Wie der Builder jetzt heißt

```python
await (
    ProviderVerification.for_provider("nutritrack-identity", identity_pact)
    .only_paths(REGISTER_PATH)
    .with_state(NO_ACCOUNT, setup=account.remove, teardown=account.remove)
    .with_state(ACCOUNT_EXISTS, setup=account.create, teardown=account.remove)
    .verify(app, pact_store)
)
```

Die Übersetzung im Einzelnen, damit der Vorgänger lesbar bleibt:

| vorher | jetzt |
| --- | --- |
| `ProviderVerifikation` | `ProviderVerification` |
| `.fuer(...)` | `.for_provider(...)` |
| `.nur_pfade(...)` | `.only_paths(...)` |
| `.mit_state(...)` | `.with_state(...)` |
| `.verifiziere(...)` | `.verify(...)` |
| `Interaktion` / `.zeigt_auf(...)` | `Interaction` / `.targets(...)` |
| `Pact.von(...)` / `.nur_auf(...)` / `.kopf` / `.inhalt` | `Pact.from_raw(...)` / `.only_on(...)` / `.head` / `.content` |
| `Zustand` / `.haelfte(...)` | `State` / `.pick(...)` |
| `Haelfte` | `Phase` |
| `_als(wert, art, wo)` | `_as(value, expected, where)` |
| `pfad` / `pfade` / `REGISTER_PFAD` | `path` / `paths` / `REGISTER_PATH` |
| `KEIN_KONTO` / `KONTO_EXISTIERT` | `NO_ACCOUNT` / `ACCOUNT_EXISTS` |
| `pact_ablage` (Fixture) / `Ablage` | `pact_store` / `Store` |
| `tests/contracts/testkonto.py`, `Testkonto` | `tests/contracts/account.py`, `Account` |
| `Testkonto.anlegen()` / `.entfernen()` | `Account.create()` / `.remove()` |
| `test_die_registrierung_erfuellt_den_identity_vertrag` | `test_registration_fulfils_the_identity_contract` |
| `test_zwei_interaktionen_mit_demselben_state_stoeren_einander_nicht` | `test_two_interactions_sharing_a_state_do_not_interfere` |

**`Testkonto` heißt `Account` und nicht `TestAccount`.** pytest sammelt Klassen mit dem Präfix
`Test` als Testklassen ein; der alte Name brauchte deshalb ein `__test__ = False`. Mit `Account`
fällt der Grund für den Riegel weg, und der Riegel mit ihm.

## Was das nicht ändert

Am Verhalten nichts. Der Lauf gegen den echten Identity-Vertrag ist weiterhin rot mit denselben
fünf Register-Interaktionen und denselben Abweichungen; der Lauf gegen den Mechanik-Pact ist
weiterhin grün. Nachgeprüft: `1 failed, 282 passed`, wobei das eine `failed` genau der im
Vorgänger beschriebene Soll-Rotlauf ist.

Ebenfalls Englisch gezogen wurde der Kommentar in [`.gitattributes`](../../.gitattributes) über die
byteweise unangetastete Ablage der Vertragsdateien. Deutsche Kommentare in `src/` und in
`make.ps1` sind bekannt und **nicht** Teil dieser Entscheidung; sie werden bei Gelegenheit der
Bearbeitung nachgezogen.
