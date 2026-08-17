# Die Claude-Seite dieses Repos

Einstieg für alle, die `.claude/` zum ersten Mal ansehen: **was dort liegt und wer es liest.**
Wie die Teile im Einzelnen arbeiten, steht in ihren eigenen Dateien — hier stehen nur die Zeiger.

## Voraussetzungen prüfen

```powershell
./make.ps1 claude-doctor
```

Meldet fehlende externe Werkzeuge (`uv`, `gh`, `semble`) und Hook-Kommandos in
`.claude/settings*.json`, die auf nicht existierende Dateien zeigen. Exit-Code 1, wenn etwas
fehlt. Die Prüfung selbst ist ein eigenständiges uv-Script
([`scripts/claude_doctor.py`](../../scripts/claude_doctor.py), `requires-python >= 3.14`, keine
Abhängigkeiten) — der Task-Runner ist nur die Hülle, ohne `pwsh` läuft sie über
`uv run --script scripts/claude_doctor.py` oder direkt als `./scripts/claude_doctor.py`.
`--demo` fährt ihren Selbsttest.

## Der Weg eines Tickets

Ein Ticket unter der Map [#40](https://github.com/mbalzert1978/fit_back/issues/40) läuft als
Pipeline:

> Issue → Worktree → `Task.md` → Entwickler-Agent → Struktur-Vorabprüfung → QA-Gate →
> Tiefen-Struktur-Review → Security-Gate → Push + PR → Cleanup

Diese Pipeline ist **nicht** hier beschrieben, sondern genau einmal, dort wo sie ausgeführt wird:
[`.claude/agents/fit-back-teamlead.md`](../../.claude/agents/fit-back-teamlead.md) — Schrittfolge,
Wellen, Concurrency-Cap, Fix-Verify-Loop und Eskalationsregeln.

## Die Bausteine

| Was | Wo | Wer liest es |
| --- | --- | --- |
| Projektregeln für den Agenten | [`CLAUDE.md`](../../CLAUDE.md) | jede Session automatisch |
| Coding-Standards | [`.rules/`](../../.rules/) | Entwickler-Agent und die Review-Gates |
| Agenten-Rollen | [`.claude/agents/`](../../.claude/agents/) | das `Agent`-Tool, per Name |
| Skills (Planung, Review, Lint, Worktrees) | [`.claude/skills/`](../../.claude/skills/), Index in [`.claude/skills/CLAUDE.md`](../../.claude/skills/CLAUDE.md) | Sessions und Agenten, per Aufruf |
| Hooks | [`.claude/hooks/`](../../.claude/hooks/), verdrahtet in [`.claude/settings.json`](../../.claude/settings.json) | die Laufzeit, vor jedem passenden Tool-Aufruf |
| Worktrees der laufenden Tickets | `.claude/worktrees/` (nicht getrackt) | die Pipeline |
| Konventionen, auf die Skills sich stützen | [`docs/agents/`](../agents/) | die Skills |

**Hooks** sind der einzige Teil, der ungefragt läuft. Aktuell zwei, beide `PreToolUse`:
`forbid-write-outside-worktree.py` verhindert, dass ein Worktree-Agent im Haupt-Checkout schreibt;
`prefer-jq-over-grep-json.py` schiebt JSON-Abfragen von `grep` auf `jq`. Warum genau diese zwei und
warum die anderen gelöscht wurden, steht in [`docs/decisions/`](../decisions/).

**Ein einziger Tracker:** Backend-Bau, Planung und Claude-Setup liegen alle als GitHub-Issues.
Der frühere Markdown-Tracker unter `docs/issues/` ist am 2026-08-17 abgeschafft worden — siehe
[`docs/agents/issue-tracker.md`](../agents/issue-tracker.md) für die Kommandos.
