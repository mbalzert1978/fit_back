# Rules

Die verbindlichen Coding-Standards dieses Repos. Eine **gemeinsame** Schicht plus je ein
**sprachspezifisches** Verzeichnis.

## Aufbau

```text
.rules/
├── common/          # sprachunabhängige Prinzipien
│   ├── anti-anemic-domain.md
│   ├── coding-style.md
│   ├── docstrings-und-kommentare.md
│   ├── escalation.md
│   ├── git-workflow.md
│   ├── patterns.md
│   ├── performance.md
│   └── security.md
└── python/          # der Stack dieses Repos — Einstieg: python/README.md
```

- **`common/`** trägt allgemeine Prinzipien ohne sprachspezifische Beispiele.
- **`python/`** erweitert sie um die Muster, Werkzeuge und Codebeispiele dieses Stacks. Der Index
  dort ([`python/README.md`](python/README.md)) nennt die empfohlene Lesereihenfolge.

## Geltungsbereich

Diese Regeln gelten fuer **allen** Python-Code dieses Repos: `src/`, `tests/`, `alembic/`,
`scripts/` und die `specs/`-Ordner. Testcode ist Code.

Das stand hier lange nicht, und die Werkzeuge sagten das Gegenteil: `pyproject.toml` schaltete mit
`"tests/**" = ["ALL"]` jede ruff-Regel in `tests/` ab, und `make.ps1` richtete `ty` und
`complexipy` nur auf `src`. Eine Testfunktion mit kognitiver Komplexitaet 46 lief so unbemerkt mit
— die Schwelle ist 15. Siehe
[`docs/decisions/2026-08-27-1400-testcode-ist-code.md`](../docs/decisions/2026-08-27-1400-testcode-ist-code.md).

Ausgenommen bleibt nur, was am Testidiom scheitert, und zwar einzeln benannt in
`pyproject.toml` statt pauschal: `S101` (`assert` ist der Test), `D1` (der Testname traegt die
Beschreibung), `PLR2004` (der erwartete Wert ist die Zusicherung), `S105`/`S106` (Testdaten sind
keine Geheimnisse).

## Vorrang

Widersprechen sich eine sprachspezifische und eine gemeinsame Regel, **gewinnt die
sprachspezifische** — das Speziellere schlägt das Allgemeinere. Innerhalb von `python/` gilt
dasselbe: die Aggregatwurzel-Regel aus `python-feature-slices.md` schlägt die generische
Zustand/Verhalten-Trennung aus `python-code-organization.md`.

### Beispiel

`common/coding-style.md` fordert Unveränderlichkeit als Grundhaltung. Eine sprachspezifische Datei
darf das für ihre Sprache überschreiben, wo das Idiom dagegen steht — dann steht die Abweichung
dort und begründet sich, statt die gemeinsame Regel stillschweigend zu verletzen.
