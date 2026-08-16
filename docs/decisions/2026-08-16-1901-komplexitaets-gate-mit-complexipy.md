# Komplexitäts-Gate mit complexipy

## Was entschieden wurde

`complexipy` wird ein Prüfschritt der Pipeline. Neues Target `./make.ps1 complexity`
(`uvx complexipy -f src`), eingehängt in `ci` zwischen `import-lint` und `test`.

## Warum

Kognitive Komplexität je Funktion ist die eine Eigenschaft, die weder ruff noch import-linter
noch die Tests messen: ruff prüft Stil und einzelne Muster, import-linter die Grenzen zwischen
den Contexts, die Tests das Verhalten. Eine Funktion darf all das bestehen und trotzdem
unlesbar sein. Der Schwellwert ist der Default des Werkzeugs (15) — kein eigener Wert, solange
kein Fall zeigt, dass er falsch liegt.

`uvx` statt Projekt-Dependency: das Werkzeug prüft den Code, es gehört nicht zu seiner
Laufzeit; `pyproject.toml`/`uv.lock` bleiben davon unberührt.

`-f` (nur gescheiterte Funktionen) statt der vollen Liste: die Ausgabe eines grünen Laufs ist
sonst mehrere hundert Zeilen, in denen das eine rote Ergebnis untergeht.

## Was der erste Lauf gefunden hat

Genau einen Verstoß in ganz `src`: `get_language_from_header` in `src/api/i18n.py` bei 28. Die
Funktion trug bereits ein `# noqa: C901, PLR0912` — die Komplexität war bekannt und per Ausnahme
durchgewunken. Genau das macht das Gate sichtbar: eine Ausnahme, die niemand mehr prüft, ist
keine Entscheidung, sondern ein Rest.

Sie wurde zerlegt statt den Schwellwert anzuheben, und dabei vom imperativen Aufsammeln auf
declarative Auswertung umgestellt: `_quality_of` (q-Gewicht eines Range), `_range_of` (Eintrag ⇒
Tag + Gewicht, Wildcard und Leeres fallen weg), `_supported_form_of` (Tag ⇒ unterstützte Sprache
oder None), und darüber ein `get_language_from_header`, das nur noch mapt, stabil nach Gewicht
sortiert und den ersten Treffer nimmt. Das `noqa` ist damit weg, alle 280 Tests bleiben grün.
