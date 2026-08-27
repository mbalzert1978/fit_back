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

## Vorrang

Widersprechen sich eine sprachspezifische und eine gemeinsame Regel, **gewinnt die
sprachspezifische** — das Speziellere schlägt das Allgemeinere. Innerhalb von `python/` gilt
dasselbe: die Aggregatwurzel-Regel aus `python-feature-slices.md` schlägt die generische
Zustand/Verhalten-Trennung aus `python-code-organization.md`.

### Beispiel

`common/coding-style.md` fordert Unveränderlichkeit als Grundhaltung. Eine sprachspezifische Datei
darf das für ihre Sprache überschreiben, wo das Idiom dagegen steht — dann steht die Abweichung
dort und begründet sich, statt die gemeinsame Regel stillschweigend zu verletzen.
