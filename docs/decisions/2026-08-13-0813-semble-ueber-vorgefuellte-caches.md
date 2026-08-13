# semble läuft über vorgefüllte Caches — kein MCP, kein Setup-Skript

**Datum:** 2026-08-13, 08:13
**Status:** entschieden
**Herkunft:** [Wayfinder-Ticket #22](https://github.com/mbalzert1978/fit_back/issues/22), Kind der
[Wayfinder-Map #25](https://github.com/mbalzert1978/fit_back/issues/25)

## Der Anlass

Das Ticket fragte: *„Wie wird der `semble`-MCP-Server projektlokal verfügbar, ohne die `.mcp.json`
an eine einzelne Maschine zu nageln?"* — und unterstellte damit, das Problem sei der **Aufrufweg**.
Der Befund am Ist-Zustand widerlegt beide Hälften der Prämisse.

## Die Prämisse des Tickets war in vier Punkten falsch

| Annahme des Tickets | Befund |
|---|---|
| `CLAUDE.md` verpflichtet auf `mcp__semble__search` | Nein. [`CLAUDE.md`](../../CLAUDE.md) erwähnt semble nicht, laut `git log -S` nie. |
| semble ist als MCP-Server konfiguriert | Nein, nirgends. Kein `.mcp.json` im Repo (auch nie eines in der History), kein Eintrag in der globalen User-Config. Das Tool `mcp__semble__search` existierte hier nie. |
| semble ist global konfiguriert | Ja, aber anders: als **Subagent** `~/.claude/agents/semble-search.md` (Tools: Bash, Read), der die **CLI** ruft. |
| Der Aufrufweg ist das Problem | Nein. semble war durch **zwei Proxy-Probleme** blockiert, siehe unten. |

Die vermutete Verpflichtung steht tatsächlich in zwei getrackten Skills —
[`docs-code-consistency/SKILL.md`](../../.claude/skills/docs-code-consistency/SKILL.md) („prefer …
MCP / CLI", mit grep-Fallback) und
[`verify-issue-breakdown/SKILL.md`](../../.claude/skills/verify-issue-breakdown/SKILL.md) („if
available … **Not yet wired up**"). Beide nennen ein Tool, das es auf dieser Maschine nie gab.

## Der tragende Befund: zwei Proxy-Probleme, keines über Umgebungsvariablen lösbar

**(A) TLS beim Modell-Download.** semble lädt beim ersten Lauf `minishlab/potion-code-16M` vom
HuggingFace-Hub. Der Fortinet-CA der Unternehmens-Interception ist ein selbstsigniertes Root
**ohne Subject und ohne Authority Key Identifier**. Pythons TLS-Stack lehnt es nach
RFC-5280-strict ab — in *jedem* Bündel. Durchprobiert und alle gescheitert:

| Bündel | Zertifikate | Ergebnis |
|---|---|---|
| Standard (certifi) | 130 | `self-signed certificate in certificate chain` |
| `fortinet-ca.pem` allein | 1 | `Missing Authority Key Identifier` |
| `firmen-ca.pem` allein | 12 | `self-signed certificate in certificate chain` |
| certifi + alle Firmen-CAs | 133 | `Missing Authority Key Identifier` |

`SSL_CERT_FILE` und `REQUESTS_CA_BUNDLE` sind hier also **keine Lösung**. Browser und
Windows-Trust-Store akzeptieren dasselbe Zertifikat — Python nicht.

**(B) tree-sitter-Parser.** `tree-sitter-language-pack` lädt seine Parser erst zur Laufzeit von
GitHub-Releases. Der Downloader steckt in `_native.pyd`, einer **Rust-Erweiterung mit eingebauten
rustls-Roots**: sie liest weder `SSL_CERT_FILE` noch den Windows-Store. Folge im Betrieb:
`Language python not found, falling back to line chunking` — semble arbeitete zeilenweise statt
syntaxbewusst.

**Was der lokale px-Proxy löst und was nicht.** px übernimmt die Proxy-Authentifizierung:

| | ohne px | mit px |
|---|---|---|
| `curl` → huggingface.co | 200 | 200 |
| `curl` → GitHub-Release-CDN | 000 (Sperrprüfung) | 200, mit `--ssl-revoke-best-effort` |
| Python/rustls → GitHub | **407** Proxy Auth | `invalid peer certificate: UnknownIssuer` |

px räumt das 407 ab. Die **Zertifikatsprüfung** bleibt in beiden Fällen verschlossen. Damit ist der
Weg vorgezeichnet: **`curl` durch px holt, Python liest nur noch lokal.**

**Der Fehlermodus ist die eigentliche Gemeinheit.** semble beendet sich bei genau diesem Fehler mit
**Exit-Code 0** und leerem Ergebnis. Ein Agent kann „kaputt" nicht von „nichts gefunden"
unterscheiden — deshalb blieb der Defekt so lange unbemerkt.

## Die Entscheidung

**1. Der Aufrufweg wird ein projektlokaler Subagent, kein MCP-Server.**
`.claude/agents/semble-search.md` wird im Repo getrackt und ruft die CLI. Gegen MCP sprechen drei
Dinge: es kostet **einen Serverprozess je Session** — genau die Dauerkosten, die die Map unter
*Hook-Latenz* schon als Sorge führt; `semble[mcp]` ist gar nicht installiert; und der Subagent hält
die Suchergebnisse in seinem eigenen Kontext statt im Hauptkontext, was der Sinn des Werkzeugs ist.

Damit ist zugleich die Nebel-Frage *„Braucht `.mcp.json` einen Fallback, wenn `semble` fehlt?"*
gegenstandslos: **es wird keine `.mcp.json` geben.**

**2. Die Caches werden vorgefüllt, ohne Setup-Skript.** Dieses Dokument ist die Dokumentation.
Erledigt und verifiziert:

- **Modell:** `minishlab/potion-code-16M`, Revision `1b0ff71095656b23306542bbad34a09109673720`,
  64 MB, per `curl` nach
  `C:\Users\<user>\.cache\huggingface\hub\models--minishlab--potion-code-16M\snapshots\<sha>\`
  (Dateien: `config.json`, `model.safetensors`, `modules.json`, `tokenizer.json`, `README.md`;
  dazu `refs/main` mit der SHA). `HF_HUB_OFFLINE` ist **nicht** nötig — der gefüllte Cache genügt,
  huggingface_hub fällt bei Netzfehler auf ihn zurück.
- **Parser:** `parsers-windows-x86_64.tar.zst` (18 042 652 Bytes, SHA256
  `581ffa0bce18c91337e289c9fae7bc0293b8ee735d589faedab146b34796fc71`, gegen `parsers.json` des
  Releases geprüft), entpackt nach
  `C:\Users\<user>\AppData\Local\tree-sitter-language-pack\v1.6.2\libs` — **300 Sprachen**.
  Entpacken über `compression.zstd` aus der Python-3.14-Standardbibliothek, kein externes `zstd`.

Beide Downloads brauchen `--ssl-revoke-best-effort`, weil der CDN-Host hinter der Interception
keine Sperrprüfung zulässt.

**3. Ein Ausfall meldet sich laut.** Der Subagent prüft auf `Got: ConnectError` und
`Language … not found` in der Ausgabe und **meldet**, statt still auf `Grep`/`Glob` zurückzufallen.
Begründung: semble soll verbindlich sein, und eine Verbindlichkeit, deren Ausfall wie ein leeres
Suchergebnis aussieht, ist eine tote Regel — genau die Sorte, die diese Map gerade abräumt. Der
Exit-Code taugt dafür nicht (siehe oben), also wird die Ausgabe geprüft.

**4. Die Versionen werden festgenagelt.** Der Parser-Cache-Pfad trägt die Version im Namen
(`v1.6.2\libs`); ein Sprung leert ihn und wirft das Repo ohne Vorwarnung auf Zeilen-Chunking
zurück. Festgehalten wird auf: **semble 0.3.3**, **tree-sitter-language-pack 1.6.2**,
**model2vec 0.8.2**, Modell-Revision `1b0ff71…`. Ein Update ist eine bewusste, begleitete
Handlung, kein Nebenprodukt.

## Verifikation

Nach beiden Schritten, mit geleertem Index (`semble clear index`) und ohne jede
Proxy-Umgebungsvariable:

- `tree_sitter_language_pack.downloaded_languages()` → 300, `get_language()` für `python`,
  `javascript`, `powershell`, `toml`, `markdown` jeweils OK.
- Die Warnung `Language python not found` ist verschwunden.
- `semble search "Outbox Zusteller SKIP LOCKED"` liefert eine **ganze Methodengrenze**
  (`src/infrastructure/outbox/relay.py:174-215`) statt eines willkürlichen Zeilenfensters —
  syntaxbewusstes Chunking ist nachweislich aktiv.
- `semble search "Result Typ im shared kernel"` findet
  `src/contexts/shared_kernel/result.py:43-66` als besten Treffer.

## Was bewusst offen bleibt

- **Wo die Verbindlichkeit steht** — `CLAUDE.md`, die Skills oder die Agent-Beschreibung. Der
  Wortlaut gehört zu [*Was bleibt in CLAUDE.md, was wird zum Link?*](https://github.com/mbalzert1978/fit_back/issues/27),
  dem Ticket, das die Destination der Map trägt. Hier wird dem nicht vorgegriffen.
- **`semble savings` bricht mit einem Traceback ab.** Ein eigener Defekt des Werkzeugs, die Suche
  ist nicht betroffen. Nicht weiter verfolgt.

## Zwei Umgebungsbefunde, die nicht ins Repo gehören

Beim Aufklären gefunden, außerhalb der Domäne dieser Map, hier nur als Fundstelle vermerkt:

- Die Proxy-Umgebungsvariablen der Maschine tragen Zugangsdaten im Klartext, sichtbar für jeden
  Prozess, der `env` liest. Gehört rotiert; px macht sie ohnehin entbehrlich.
- `NODE_EXTRA_CA_CERTS` zeigt auf einen nie ersetzten Platzhalterpfad, die Datei existiert nicht.
  Betrifft Node-Werkzeuge, nicht Python.
