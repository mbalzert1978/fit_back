# Kein ruff-Hook nach dem Edit — ruff kommt in die Struktur-Vorabprüfung

**Datum:** 2026-08-13, 07:39
**Status:** entschieden
**Herkunft:** [Wayfinder-Ticket #17](https://github.com/mbalzert1978/fit_back/issues/17), Kind der
[Wayfinder-Map #25](https://github.com/mbalzert1978/fit_back/issues/25)
**Vorgänger:** [Wann ein Hook seine Existenz verdient](2026-08-13-0641-hook-kriterium-und-abschied-von-den-dotnet-hooks.md)
— dessen Kriterium wird hier unverändert angewandt und um seine allgemeine Kehrseite ergänzt.

## Der Anlass

Der Ursprungsartikel verdrahtet den Linter als `PostToolUse`-Hook direkt auf `Edit|Write`. Für
dieses Repo hieße das: ein neues `.claude/hooks/ruff-after-edit.py`, das nach jedem Edit `ruff`
auf der geänderten Datei laufen lässt. Das Versprechen: ein Verstoß fällt Sekunden statt Minuten
später auf, und der Agent sieht das Ergebnis noch im eigenen Kontext.

## Der tragende Befund: die vermutete Lücke war die falsche

Die Frage unterstellte, das Problem sei **Latenz** — der Verstoß falle „erst in der CI" auf, und
ein Hook hole ihn Minuten nach vorn. Die Messung am Ist-Zustand zeigt etwas anderes.

`ruff` läuft in der Ticket-Pipeline aus [`.claude/agents/fit-back-teamlead.md`](../../.claude/agents/fit-back-teamlead.md)
**kein einziges Mal**, bis der PR steht:

| Pipeline-Schritt | Was dort läuft | ruff dabei? |
|---|---|---|
| 4 Struktur-Vorabprüfung | `./make.ps1 import-lint`, `structure-placement-check`, `slice-shape-check` | nein |
| 5 QA-Gate | `review-against-rules`, `qa-check`, `solid-principles-check` | nein |
| 6 Tiefen-Struktur-Review | `thermo-nuclear-code-quality-review` | nein |
| 7 Security-Gate | `review-against-rules` auf `.rules/common/security.md` | nein |
| 9 Push + PR | — | — |
| danach | GitHub Actions, [`ci.yml`](../../.github/workflows/ci.yml) → `./make.ps1 ci` | **erstmals ja** |

Das Skill `lint-and-format-check` existiert, steht aber in keinem Gate; es gehört zum
`validate-fix-loop`. Der erste Ort, an dem ein ruff-Verstoß auffällt, liegt also **hinter der
kompletten Gate-Kaskade** — nicht „Minuten später", sondern eine ganze Pipeline später.

Die Lücke ist damit kein Latenz-, sondern ein Gate-Problem. Und ein Loch in einem Gate schließt
man mit einem Gate-Schritt, nicht mit einem Hook.

## Die Entscheidung

**Nein — es wird kein `PostToolUse`-ruff-Hook gebaut.** `.claude/hooks/ruff-after-edit.py` entsteht
nicht.

Er scheitert an Punkt (a) des Kriteriums: `./make.ps1 ci` prüft dieselbe Sache strukturell und
vollständig. Dazu kommen drei Befunde, die je für sich gegen den Hook stehen:

- **Der vorgeschlagene Umfang wäre zur Hälfte leer.** Der Vorschlag lautete „nur `.py` unter `src/`
  oder `tests/`". [`pyproject.toml`](../../pyproject.toml) setzt für `tests/**` und
  `src/contexts/*/specs/**` aber `per-file-ignores = ["ALL"]` — ein Lint-Hook fände dort
  strukturell nichts.
- **`--fix`/`format` zerstören die Zustandskohärenz.** Ein `PostToolUse`-Hook schreibt die Datei
  *nach* dem Edit um; die Harness kennt danach einen veralteten Stand, und der nächste Edit auf
  dieselbe Datei läuft in „file modified since read".
- **Der Preis fällt je Edit an, der Nutzen je Ticket.** Gemessen in diesem Repo (warm):
  `.venv/Scripts/ruff.exe check <datei>` 0,47 s, `uv run ruff check <datei>` 0,65 s, kalt 3,5 s.
  Ein Python-Hook via `uv run` legt die in
  [#18](https://github.com/mbalzert1978/fit_back/issues/18) gemessenen 852–907 ms Prozessstart
  obendrauf.

## Was stattdessen passiert

An zwei Stellen, beide ohne neuen Hook:

1. **`./make.ps1 lint` und `./make.ps1 format-check` als Direktaufrufe in Schritt 4**
   (Struktur-Vorabprüfung), neben das dort schon stehende `./make.ps1 import-lint`. Verstoß →
   sofort zurück an den Entwickler-Agenten, kein Weiterlauf in Schritt 5/6. Das ist genau die
   Begründung, die für Schritt 4 ohnehin schon im Agenten-Dokument steht: mechanische Fehler sollen
   keine ganze Gate-Runde kosten.
2. **Eine Zeile in die `Task.md` des Entwickler-Agenten:** beide Ziele müssen vor der Übergabe grün
   sein. Das ist das, was von „Sekunden statt Minuten" übrig bleibt — der Fund wandert zum
   Verursacher, ohne Latenz je Edit. Das Gate aus Punkt 1 bleibt trotzdem: eine Prompt-Zeile ist
   keine Garantie.

Bewusst **nicht** gewählt:

- **Das Skill `lint-and-format-check` statt der Direktaufrufe.** Seine
  [`config.json`](../../.claude/skills/lint-and-format-check/config.json) fährt exakt dieselben
  zwei Kommandos (`uv run ruff check .` / `uv run ruff format --check .`). Schritt 4 ist
  ausdrücklich als „deterministische Checks ohne LLM-Urteil" definiert und ruft `make.ps1` schon
  direkt auf; der Direktaufruf fügt sich dort ohne Bruch ein. Das Skill bleibt, wofür es gebaut
  ist: der `validate-fix-loop`.
- **`./make.ps1 ci` komplett als Gate-Schritt.** Es zöge einen zweiten vollen Testlauf nach sich,
  den `qa-check` schon fährt, und ein zweites `import-lint`, das in Schritt 4 schon steht.
- **Nur `lint` ohne `format-check`.** Das ließe die Hälfte der Lücke offen —
  Formatierungsverstöße fielen weiterhin erst in der GitHub-CI auf.

Beide gewählten Kommandos schreiben nichts (`ruff check` ohne `--fix`, `ruff format --check`). Die
Sorge, ein Werkzeug könnte Dateien hinter dem Rücken des Agenten umschreiben, entfällt auf diesem
Weg vollständig.

## Die allgemeine Regel, die daraus folgt

Diese Entscheidung ist der erste Anwendungsfall einer Regel, die ab jetzt allgemein gilt und die
nur die Kehrseite von Punkt (a) des Hook-Kriteriums ist:

> **Was `./make.ps1 ci` schon fährt, wird nie Hook — höchstens Gate-Schritt.**

Ein Vorschlag der Bauart „Werkzeug X nach jedem Edit als Hook" ist damit ohne neue Runde erledigt,
sobald X in `ci` steht. Ein Markdown-Formatter, ein `import-lint`-Hook, ein Test-nach-Edit-Hook
fallen alle darunter.

Die Regel greift **nicht** auf [#20 Worktree-Guard](https://github.com/mbalzert1978/fit_back/issues/20):
ein Worktree-Guard prüft, *wohin* geschrieben wird. Das kann `ci` strukturell nicht sehen, und
damit bleibt Punkt (a) des Kriteriums dort offen — die Frage wird eigenständig entschieden.

## Was danach kommt

Die **Umsetzung** — Schritt 4 im Pipeline-Dokument ergänzen und die Zeile ins
`Task.md`-Template — läuft über die normale Ticket-Pipeline, nicht über die Wayfinder-Map; so
steht es in deren Destination.
