---
name: reflect
description: "End-of-session experience extraction. Scans the conversation for corrections, validated approaches, and architectural decisions, then persists them as structured experience files with decay metadata. Run automatically via hook after commits/deploys, or manually anytime."
---

# Reflect — Experience Extraction Skill

Implements the outer loop of the dual-loop agent architecture. Extracts durable lessons from the current conversation and persists them as structured experience memory files.

**Repo-local override:** this project's `CLAUDE.md` prohibits using Claude Code's cross-session memory system — no entries under `~/.claude/projects/<project-hash>/memory/`, in this project or any other out-of-repo store. Instead, experiences live under **`docs/reflections/`** in the repo itself (`docs/reflections/exp_<name>.md`, flat, no `experiences/` subfolder), are committed like any other repo file, and the index lives at `docs/reflections/README.md` (not `MEMORY.md`). Everywhere below that says "memory directory" or `memory/experiences/`, read it as `docs/reflections/`. If you ever work in a project without this override, fall back to the generic behavior: locate the harness's memory directory (in Claude Code, typically `~/.claude/projects/<project-hash>/memory/`) and use its `MEMORY.md`/`experiences/` layout instead.

## Phase 1: EXTRACT

Scan the current conversation for experiences worth persisting. Three categories, in priority order:

### 1. Corrections (highest priority)
**Signals:** User said "no", "don't", "stop", "that's wrong", rejected a tool call, or redirected your approach.
**Memory type:** `feedback`

### 2. Validated Approaches (medium priority)
**Signals:** User confirmed a non-obvious choice ("yes exactly", "perfect"), accepted an unusual approach without pushback, or an approach succeeded where alternatives existed.
**Memory type:** `feedback`

### 3. Architectural Decisions (lower priority)
**Signals:** A design choice was discussed and settled, or a non-obvious technical constraint was discovered during implementation.
**Memory type:** `project`

### Extraction rules
- For each candidate, ask: *"Would this be useful in a FUTURE conversation, or is it only relevant right now?"*
- Discard anything already captured in existing memory files or derivable from code/git
- Discard ephemeral task details, debugging steps, or conversation-specific context

### Deduplication (two-layer)
1. **Primary:** Read all files in `docs/reflections/`. Check the `name` field in frontmatter. If a new experience matches an existing `name`, do NOT create a new file — instead update the existing file's `frequency` (increment by 1) and `last_triggered` (set to today's date).
2. **Secondary:** Search `docs/reflections/` file bodies for keyword overlap. If strong overlap is found with a differently-named experience, flag it in the Phase 4 report with: `"Possible duplicate: <new> overlaps with <existing> — review manually"`. Do NOT auto-merge.
3. **Frequency bump:** If the session involved a topic that an existing experience covers — even if no correction happened — bump that experience's `frequency` and `last_triggered`. This keeps relevant experiences alive.

Also skip anything already fully captured in a `docs/decisions/` entry — link to it from `**Why:**` instead of duplicating its narrative (see the existing `exp_*.md` files under `docs/reflections/` for the pattern).

## Phase 2: PERSIST

For each new experience from Phase 1:

### File creation
- **Location:** `docs/reflections/exp_<kebab-case-name>.md`
- **Format:** read `assets/experience_template.md` and fill its placeholder tokens — don't reconstruct the format from memory. The tokens:
  - `{{NAME}}` — kebab-case identifier
  - `{{DESCRIPTION}}` — one-line summary, specific enough to judge relevance in future conversations
  - `{{TYPE}}` — `feedback` or `project`
  - `{{TODAY}}` — today's date as `YYYY-MM-DD`
  - `{{DECAY_ELIGIBLE}}` — `true`, or `false` ONLY for critical safety rules (deploy safety, data destruction prevention, credential handling)
  - `{{RULE}}` — the rule or fact, one clear statement
  - `{{WHY}}` — the reason: incident, constraint, or user preference that caused this
  - `{{HOW_TO_APPLY}}` — when this kicks in and what to do

### Memory index update
- Add a pointer to the new file under the `## Experiences` section of `docs/reflections/README.md`
- Format: `- [exp_<name>.md](exp_<name>.md) — <one-line description>` (flat path, no `experiences/` prefix)
- Keep entries sorted alphabetically within the section

### For existing experience updates (frequency bumps)
- Edit the existing file's frontmatter: increment `frequency`, set `last_triggered` to today
- Do NOT modify the body content unless the experience needs refinement based on new information

## Phase 3: DECAY

The date arithmetic is **not** done by hand — run the bundled script, then act on its JSON. It scans the experiences dir (and its `archived/` subdir), parses each file's frontmatter, computes `days_since = today - last_triggered`, and applies the configured thresholds:

```bash
uv run .claude/skills/reflect/scripts/decay_sweep.py --memory-dir docs/reflections --pretty
```

Thresholds and the experiences dir live in the bundled `config.json` (`archive_after_days` 90, `stale_flag_after_days` 60, `archive_min_frequency` 3, `experiences_dir` — set to `.` for this repo-local override, since `docs/reflections/` files sit flat with no `experiences/` subfolder). The script reads them; don't restate the numbers from prose.

The report has four lists — `archive`, `flag_stale`, `unarchive`, `skipped` (the last two are informational). Files with `decay_eligible: false` never reach an action list (they land in `skipped`). **Act** on each list:

- **`archive`** — for each entry (`days_since > archive_after_days` AND `frequency < archive_min_frequency`):
  - Move the file to `docs/reflections/archived/`
  - Remove its pointer from `docs/reflections/README.md`
  - Add to the Phase 4 report: `"Archived exp_X.md (last relevant N days ago, triggered M times)"`
- **`flag_stale`** — for each entry (`days_since > stale_flag_after_days`, not archive-bound): if the index entry doesn't already carry a stale marker, prepend a stale warning to it.

### Recovery
The script lists archived files that are relevant again under `unarchive`. Also un-archive when Phase 1 extraction surfaces a topic matching an archived experience. For each:
- Move from `docs/reflections/archived/` back to `docs/reflections/`
- Reset `last_triggered` to today, increment `frequency`
- Re-add pointer to `docs/reflections/README.md`

## Phase 4: REPORT

Print a terse summary. Keep it short — this fires after commits/deploys, it shouldn't dominate the conversation.

**Format:**
```
Reflect: <N> new experiences, <M> updated, <K> archived

New:
- exp_<name>.md — <description>

Updated:
- exp_<name>.md — frequency <old>→<new>

Archived:
- exp_<name>.md — last relevant <N> days ago
```

If there are possible duplicates from Phase 1 dedup, append:
```
Possible duplicates (review manually):
- <new experience> overlaps with <existing experience>
```

### No-op case
If the session had no corrections, no validated approaches, and no architectural decisions:
- Skip Phases 1-2
- Still run Phase 3 (decay sweep)
- Print: `"Reflect: no new experiences. Decay sweep: <result>."`
