# Ressourcen und Kontext

## Modellwahl

**Haiku** — leichte Agenten mit häufigem Aufruf, Codegenerierung im Paar, Arbeiter-Agenten in
Mehr-Agenten-Systemen.

**Sonnet** — die eigentliche Entwicklungsarbeit, das Orchestrieren von Mehr-Agenten-Abläufen,
komplexe Programmieraufgaben.

**Opus** — komplexe Architekturentscheidungen, Aufgaben mit dem höchsten Denkbedarf, Recherche und
Analyse.

Das Modell wird an der Aufrufstelle gewählt, nicht global vorbelegt.

## Kontextfenster

Die letzten 20 % des Kontextfensters meiden bei:

- großflächigem Refactoring
- Implementierungen über mehrere Dateien hinweg
- der Fehlersuche in verschränkten Abläufen

Weniger kontextempfindlich sind:

- Änderungen an einer einzelnen Datei
- das Anlegen eigenständiger Hilfsmittel
- Aktualisierungen der Dokumentation
- einfache Fehlerkorrekturen

## Erweitertes Denken

Erweitertes Denken ist standardmäßig aktiv. Steuerung:

- **Umschalten**: Option+T (macOS) bzw. Alt+T (Windows/Linux)
- **Konfiguration**: `alwaysThinkingEnabled` in `~/.claude/settings.json`
- **Obergrenze**: `MAX_THINKING_TOKENS`
- **Sichtbar machen**: Ctrl+O

Bei Aufgaben mit hohem Denkbedarf: erweitertes Denken sicherstellen, den Plan-Modus nutzen, mehrere
Kritikrunden fahren und für unterschiedliche Blickwinkel Subagenten mit getrennten Rollen einsetzen.

## Wenn der Build scheitert

1. Fehlermeldungen lesen
2. Schrittweise korrigieren
3. Nach jedem Schritt nachprüfen
