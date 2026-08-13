# Issue tracker: GitHub

> **Zur Sprache dieser Datei:** Sie ist in Englisch gehalten, weil sie zur repo-übergreifend
> wiederverwendeten Skill-Infrastruktur gehört und nicht zum fachlichen Inhalt dieses Projekts —
> dieselbe Ausnahme, die `CLAUDE.md` für `.claude/skills/`-Definitionen und deren `config.json`
> macht. Ihre Überschriften sind das, wonach die portablen Skills suchen; eine Übersetzung
> brächte nur Drift. Der repo-spezifische Teil steht unter „Live wayfinding efforts".

Issues and specs for this repo live as GitHub issues (`mbalzert1978/fit_back`). Use the `gh` CLI
for all operations; it infers the repo from `git remote -v` when run inside the clone.

**This file was written retroactively on 2026-08-13.** The convention below was already in use —
map [#25](https://github.com/mbalzert1978/fit_back/issues/25) and its children predate it — but no
one had ever run `/setup-matt-pocock-skills`, so nothing recorded it. A session then reasoned from
this file's absence to "no tracker in use", defaulted to local markdown, and reported that no map
existed without ever querying GitHub for one. **The absence of a config file is not evidence about
the tracker. Look for the artifact, not the configuration** — see "Before assuming there is no map"
below.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Note that `gh issue view <n> --comments` has been observed returning empty output in this
environment; `gh issue view <n> --json number,title,body,labels,state,url,comments` works and is
the safer call.

### Not the same thing as `docs/issues/`

This repo also carries [`docs/issues/`](../issues/) — the tracer-bullet issues that implement the
milestones, tracked as markdown files with their own `issue-status` / `issue-close` skills. Those
are a **separate** system from GitHub issues and are not affected by anything in this file. GitHub
issues here carry planning and Claude-setup work; `docs/issues/` carries the backend build.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

GitHub shares one number space across issues and PRs, so a bare `#42` may be either — resolve with
`gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --json number,title,body,labels,state,url,comments`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Destination / Notes /
  Decisions-so-far / Fog body. `gh issue create --label wayfinder:map`.
- **Child ticket**: a GitHub **sub-issue** of the map. List them with
  `gh api repos/mbalzert1978/fit_back/issues/<map>/sub_issues`. Labels: `wayfinder:<type>`
  (`research` / `prototype` / `grilling` / `task`). Once claimed, the ticket is assigned to the
  driving dev.
- **Blocking**: GitHub's **native issue dependencies**. Add an edge with
  `gh api --method POST repos/mbalzert1978/fit_back/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`,
  where `<blocker-db-id>` is the blocker's numeric **database id**
  (`gh api repos/mbalzert1978/fit_back/issues/<n> --jq .id` — _not_ the `#number` or `node_id`).
  The live gate is `issue_dependencies_summary.blocked_by`, which counts **open** blockers only.
- **Frontier query** — open, unblocked, unclaimed children, first in map order wins:

  ```bash
  gh api repos/mbalzert1978/fit_back/issues/<map>/sub_issues \
    --jq '.[] | select(.state=="open" and .issue_dependencies_summary.blocked_by==0 and (.assignees|length)==0) | "\(.number) \(.title)"'
  ```

- **Claim**: `gh issue edit <n> --add-assignee @me` — the session's first write, before any work.
- **Resolve**: `gh issue comment <n> --body-file -`, then `gh issue close <n> --reason completed`,
  then append a context pointer (gist + link) to the map's Decisions-so-far. Edit the map body with
  `gh issue edit <map> --body-file <path>` after dumping it via
  `gh issue view <map> --json body --jq .body`.

### Before assuming there is no map

Query for the artifact, never infer from configuration:

```bash
gh issue list --label wayfinder:map --state all --json number,title,state
```

### Live wayfinding efforts

- [**#25 — Wayfinder-Map: Hook-Portfolio und semble-Anbindung des Claude-Setups**](https://github.com/mbalzert1978/fit_back/issues/25)
  — die Claude-Code-Konfiguration dieses Repos (`.claude/`, `CLAUDE.md`). Trägt ausnahmsweise auch
  die **Ausführung** ihrer Entscheidungen als `wayfinder:task`-Kinder, statt sie an die
  Ticket-Pipeline abzugeben; die Begründung steht in ihren Notes. Entscheidungen landen als Datei
  unter [`docs/decisions/`](../decisions/), auf Deutsch.

## Nicht eingerichtet

`/setup-matt-pocock-skills` ist hier nie gelaufen; diese Datei ist von Hand nachgezogen. Zwei
Geschwisterdateien, die das Skill sonst anlegt, fehlen weiterhin **mit Absicht**:

- `docs/agents/triage-labels.md` — das `triage`-Skill ist nicht installiert, die Labels hätten
  keinen Leser.
- `docs/agents/domain.md` — es beschreibt, wo `CONTEXT.md` und `docs/adr/` liegen. `docs/adr/` gibt
  es hier nicht und wird es nicht geben (die Rolle spielt `docs/decisions/`); `CONTEXT.md` liegt
  seit Ticket #34 der Map #25 im Repo-Root. #35 hat `docs-code-consistency` auf `docs/decisions/`
  umgehängt — über `decision_docs_dir` in dessen `config.json`, nicht im Skill-Text, weil
  repo-spezifische Pfade dorthin gehören. Damit ist neu zu bewerten, ob diese Datei noch fehlen
  soll: die beiden Skills, für die sie gedacht war, finden ihre Artefakte inzwischen selbst.

Ebenfalls bewusst unterlassen: der `## Agent skills`-Abschnitt, den das Setup-Skill in `CLAUDE.md`
schreiben will. #27 hat entschieden, dass `CLAUDE.md` nichts über das Repo behauptet und nur noch
verlinkt; ein Abschnitt, der den Skill-Bestand aufzählt, wäre genau so eine Behauptung. Seit der
Ausführung durch #33 verlinkt `CLAUDE.md` sowohl `docs/agents/` als auch den Skill-Index
`.claude/skills/CLAUDE.md` — die Fundbarkeit ist damit hergestellt, ohne dass etwas aufgezählt wird.
