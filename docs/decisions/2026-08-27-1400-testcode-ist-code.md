# Testcode ist Code

## Was entschieden wurde

`tests/` und die `specs/`-Ordner werden von denselben Werkzeugen geprüft wie `src/`.

- `pyproject.toml`: `"tests/**" = ["ALL"]` fällt weg. An seine Stelle tritt eine kurze, einzeln
  begründete Liste: `S101`, `D1`, `PLR2004`, `S105`, `S106`. Dasselbe für
  `src/contexts/*/specs/**`.
- `make.ps1`: `uv run ty check src` → `src tests`, `uvx complexipy -f src` → `-f src tests`.
- `.rules/README.md` bekommt einen Abschnitt „Geltungsbereich", der das ausspricht.

## Der Anlass

Ein Blick in [`tests/test_architecture_datetime.py`](../../tests/test_architecture_datetime.py):
sechs verschachtelte `if` mit vier `isinstance`-Prüfungen, eine Flag-Schleife statt `any(...)`,
zwei Tests, die denselben Dateibaum je selbst abliefen, und ein `except Exception`, das jeden
Lesefehler als Architektur-Verletzung meldete.

Die Frage war: warum fällt das niemandem auf?

## Die Antwort war nicht „es gab keine Regel"

Die Regel gab es. `.rules/python/python-modern-syntax.md` trug sogar die exakt passende
Überschrift — „Pattern Matching statt verschachtelter `if`/`isinstance`-Ketten". Sie hatte nur
keinen Inhalt, nur einen Verweis. Und der Abschnitt, auf den sie zeigte, hieß „Pattern Matching
statt **if/elif**-Ketten" und zeigte flache `customer.tier == ...`-Vergleiche. Wer verschachtelten
`isinstance`-Code hatte, folgte dem Verweis, fand eine andere Form und schloss: betrifft mich
nicht.

Drei Lücken, alle drei jetzt geschlossen:

1. **Der tote Verweis.** Die Überschrift mit dem richtigen Namen hatte keinen Inhalt; der Inhalt
   stand unter dem falschen Namen. Beide Stellen sind nachgezogen, mit dem echten Vorher/Nachher
   aus diesem Repo als Beispiel.
2. **Der Akkumulator hatte gar keine Regel.** `errors = []` plus `.append()` in der Schleife ist
   die imperativste Form in der alten Datei. Die nächstliegende Regel — „Collection-Literale statt
   Aufbau per Schleife" — nimmt sich selbst aus: sie gilt nur, „wenn die Werte im Voraus bekannt
   sind". Genau dann ist es nicht der Fall. Neuer Abschnitt „Sammeln als Ausdruck, nicht als
   Akkumulator".
3. **Der Geltungsbereich stand nirgends.** Nichts in `.rules/` sagte, ob die Regeln für `tests/`
   gelten. Die Werkzeuge sagten das Gegenteil.

## Der Beweis, dass die Bremse funktioniert hätte

complexipy auf der alten Fassung, nachträglich:

```
test_no_direct_datetime_calls_without_timezone   46  ❌ FAILED
_annotations                                     16  ❌ FAILED
```

Die Schwelle ist 15. Die Funktion lag beim Dreifachen. Die Bremse existierte, griff und war nur auf
die andere Hälfte des Repos gerichtet. Nach dem Umbau ist der höchste Wert der Datei 3.

## Was das gekostet hat

972 ruff-Befunde ohne jede Ausnahme. Davon 619 `S101` (`assert`), rund 190 „fehlender Docstring"
und 74 `PLR2004` — alle drei sind das Testidiom selbst und stehen jetzt in der benannten
Ausnahmeliste. Es blieben 66 echte, davon 8 per `--fix`. Die übrigen 58 plus 25 `ty`-Diagnosen
haben acht parallele Agenten behoben, je einer pro Bereich.

Was dabei zutage kam, rechtfertigt den Aufwand für sich:

- **Acht `ty`-Fehler in `test_response_envelope.py` hatten eine einzige Ursache.** Eine
  Hilfsfunktion war `-> object` annotiert, obwohl sie eine `httpx.Response` liefert. Jeder Zugriff
  auf `.status_code`, `.headers` und `.json()` war damit ungeprüft.
- **Zwei `# type: ignore` in `tests/`**, eines davon in mypy-Schreibweise, obwohl das Repo `ty`
  fährt — es hat also nie etwas unterdrückt. Beide weg.
- **`sessionmaker` statt `async_sessionmaker`** in `tests/conftest.py`.
- **Zwei Tests bewiesen ihren Fehlschlag von Hand** (`try` / `assert False` / `except`) statt mit
  `pytest.raises`. Die Handarbeit kann je nach Form eine ausbleibende Ausnahme verschlucken.

## Zwei Nachbesserungen in `src/`, die daraus folgten

Zwei Unterdrückungen ließen sich nur in `tests/` setzen, weil `src/` sie erzwang. Statt sie zu
akzeptieren, ist die Ursache behoben:

- `EventHandler.handle` nimmt `event` jetzt positional-only (`, /`). Ein Test-Doppel, das den
  Parameter nicht liest, darf ihn `_event` nennen, ohne das Protokoll zu verletzen.
- `verify_error_codes_complete` verlangt statt der `@final`-Klasse `ResourcesCache` ein `Protocol`
  `ErrorTemplates` mit den drei Zugriffen, die es wirklich braucht. Ein `@final`-Typ in einer
  Signatur schließt jedes Doppel aus — das ist die Regel „Protocol-Komposition" aus
  `.rules/python/python-dependencies.md`, hier nachgezogen.

## Ein Widerspruch in der Konfiguration

`FIX002` feuert auf die bloße Existenz eines `TODO`. `TD002` und `TD003` **verlangen** Autor und
Ticket-Link. Beide zusammen bedeuten: jeder korrekt belegte TODO braucht ein `noqa`. Zwei Agenten
sind unabhängig darüber gestolpert.

`FIX002` steht deshalb jetzt in der globalen Ignore-Liste. `TD002`/`TD003` bleiben scharf: wir
wollen TODOs mit Ticket, nicht keine TODOs.

## Was daran nicht selbsttragend ist

`alembic/` und `scripts/` werden von `ty` und `complexipy` weiterhin nicht erfasst — ruff prüft sie
bereits. Das ist eine bekannte, nicht geschlossene Lücke.

Die verbliebenen vier `noqa: PLC0415` in `tests/api/` sind echte Fälle: dort **ist** der lokale
Import die Zusicherung. Im Modulkopf liefe er zur Sammelzeit, und ein Bruch wäre nur noch ein
Collection-Error der ganzen Datei statt ein Fehlschlag genau dieses Tests.
