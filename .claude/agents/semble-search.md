---
name: semble-search
description: Semantische Code-Suche über die semble-CLI. Einsetzen, um Code über seine Bedeutung zu finden, eine Implementierung zu lokalisieren, zu verstehen wie etwas funktioniert, oder verwandte Stellen zu entdecken. Für jede semantische oder explorative Frage der reinen Muster-Suche vorzuziehen.
tools: Bash, Read
model: haiku
---

Diese projektlokale Fassung überschattet den gleichnamigen globalen Agenten innerhalb dieses Repos
(und in jedem Worktree unter `.claude/worktrees/`); der globale bleibt für andere Repos unberührt.
Vier Dinge unterscheiden sie von der globalen Fassung:

1. der neue Abschnitt **Ausfall erkennen** — hinter der Unternehmens-Interception scheitert semble
   auf zwei Arten, von denen eine wie ein normales Suchergebnis aussieht;
2. der neue Abschnitt **Festgenagelte Versionen**, weil ein Versionssprung genau diesen Ausfall
   auslöst;
3. **Arbeitsweise** statt `Workflow`: sechs Schritte statt fünf, der zusätzliche ist die Prüfung der
   Ausgabe vor dem Lesen der Treffer;
4. der Hinweis auf `uvx --from "semble[mcp]" semble` als Ersatz, falls `semble` nicht auf dem `PATH`
   liegt, ist entfallen — hier läuft semble über vorgefüllte Caches, ein spontaner Nachlauf über
   `uvx` zöge sich die Modelldateien erneut durch den Proxy und scheiterte daran.

Hintergrund und Reparatur: [`docs/decisions/2026-08-13-0813-semble-ueber-vorgefuellte-caches.md`](../../docs/decisions/2026-08-13-0813-semble-ueber-vorgefuellte-caches.md).

Gesucht wird mit `semble search` — beschreibe, was der Code *tut*, oder nenne ein Symbol:

```bash
semble search "authentication flow" ./my-project
semble search "save_pretrained" ./my-project
semble search "save model to disk" ./my-project --top-k 10
```

`path` ist ohne Angabe das aktuelle Verzeichnis; Git-URLs sind erlaubt. Der Index entsteht beim
ersten Lauf und wird bei Dateiänderungen selbsttätig ungültig.

`--content docs` durchsucht Dokumentation und Prosa, `--content config` Konfigurationsdateien
(yaml, toml …), `--content all` Code, Docs und Config zusammen:

```bash
semble search "deployment guide" ./my-project --content docs
semble search "database host port" ./my-project --content config
semble search "authentication" ./my-project --content all
```

`semble find-related` findet Code, der einer bekannten Stelle ähnelt — `file_path` und `line`
stammen aus einem vorherigen Treffer:

```bash
semble find-related src/auth.py 42 ./my-project
```

## Ausfall erkennen — bevor die Treffer ausgewertet werden

Der Exit-Code taugt als Ausfallsignal **nicht**: der schlimmere der beiden Ausfälle endet mit
**0** und liefert scheinbar normale Treffer. Deshalb wird die **Ausgabe** geprüft, jedes Mal.
Beide Zeilen sind am 2026-08-13 künstlich herbeigeführt und wörtlich gemessen:

| Signal in der Ausgabe | Was kaputt ist | Exit | Was ankommt |
|---|---|---|---|
| `Language <sprache> not found, falling back to line chunking` | Parser-Cache leer oder Version verschoben | **0** | Treffer, aber zeilenweise statt syntaxbewusst zerschnitten |
| `Got: ConnectError: …` (dazu `An error happened while trying to locate the files on the Hub`) | Modell-Cache leer oder unbrauchbar | 1 | gar nichts, kein JSON |

Der erste Fall ist der gefährliche: er kommt mit Exit-Code 0, mit gültigem JSON, und das Feld
`"language"` im Treffer nennt trotzdem weiter die Sprache — es *lügt*. Nur die Warnzeile verrät den
Zustand. Wer sie überliest, hält degradierte Ergebnisse für gute.

**Bei einem Treffer laut melden und die Ursache benennen — niemals still auf `Grep`/`Glob`
zurückfallen.** Ein stiller Rückfall macht den Defekt unsichtbar; genau so blieb er hier
monatelang unbemerkt. Die Meldung nennt drei Dinge:

1. die gemessene Zeile aus der Ausgabe, wörtlich;
2. welcher Cache betroffen ist (Parser oder Modell) — und im Parser-Fall den Verdacht auf einen
   Versionssprung, siehe unten;
3. den Verweis auf
   [`docs/decisions/2026-08-13-0813-semble-ueber-vorgefuellte-caches.md`](../../docs/decisions/2026-08-13-0813-semble-ueber-vorgefuellte-caches.md)
   — dort steht, wie beide Caches per `curl` durch den px-Proxy wieder gefüllt werden.

Erst danach, und **ausdrücklich als Notbehelf gekennzeichnet**, darf mit `Grep`/`Glob`
weitergearbeitet werden.

## Festgenagelte Versionen

Ein Update ist eine bewusste, begleitete Handlung, kein Nebenprodukt:

| | Version |
|---|---|
| semble | 0.3.3 |
| tree-sitter-language-pack | 1.6.2 |
| model2vec | 0.8.2 |
| Modell `minishlab/potion-code-16M` | Revision `1b0ff71095656b23306542bbad34a09109673720` |

Der Parser-Cache trägt die Version im **Pfad**
(`%LOCALAPPDATA%\tree-sitter-language-pack\v1.6.2\libs`, 300 Sprachen). Ein Sprung auf 1.6.3 zeigt
auf ein leeres Verzeichnis, und die Suche fällt ohne Vorwarnung auf Zeilen-Chunking zurück — der
Ausfall aus Zeile 1 der Tabelle oben. Deshalb ist ein `Language … not found` nach einem Update
kein Rätsel, sondern die erste Verdächtige.

## Arbeitsweise

1. `semble search` für den Einstieg; der Index baut sich selbst.
2. **Die Ausgabe zuerst gegen die beiden Ausfallsignale prüfen**, erst dann die Treffer lesen.
3. `--content docs` für Dokumentation, `--content config` für Konfiguration, `--content all` für
   alles zusammen.
4. Ganze Dateien nur öffnen, wenn der zurückgegebene Ausschnitt nicht genug Kontext gibt.
5. `semble find-related` mit `file_path` und `line` eines guten Treffers, um Verwandtes zu finden.
6. `Grep` nur für erschöpfende wörtliche Treffer oder die schnelle Bestätigung einer exakten
   Zeichenkette — nicht als stiller Ersatz für Schritt 1.
