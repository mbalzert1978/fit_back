---
name: issue-close
description: "Closes an issue by setting status to 'closed' in its frontmatter and appending a completion note to the issue file's own body. Use when the user says 'close issue X', 'issue X is done', 'mark X as erledigt', 'issue X abschließen', or indicates an issue is complete."
arguments: "Issue ID or partial filename, optionally followed by a completion note — e.g. '0021' or '0021 Resolved via Option C (ADR-0019)'. If ID is omitted, ask which issue to close before proceeding. Note defaults to the issue title if not provided."
---

# Issue Close

Closes one issue: updates frontmatter `status`, appends a completion note to the issue file itself. No central progress file is read or written — each issue holds its own completion record, so parallel branches/worktrees closing different issues never conflict on a shared file. Use the `issue-status` skill for a cross-issue overview instead.

## Process

### 1. Resolve the issue file and note
Parse `arguments`:
- Everything up to the first space (or the whole string) is the **ID/slug**.
- Everything after the first space is the **completion note** (may be empty).

Find the matching file:
```powershell
$arg = "<ID-part>"
Get-ChildItem "docs/issues" -Filter "*.md" |
  Where-Object { $_.Name -like "$arg*" -and $_.Name -ne "PROGRESS.md" }
```

If zero matches: stop — `"No issue found matching '<arg>'."`.
If multiple matches: list them and ask for a more specific ID.

### 2. Read and verify current status
Read the file with `bat "FILE" --paging=never`. Parse frontmatter.

- `status: closed` already → print `"Issue <ID> is already closed."` and stop.
- `status: open`, `status: blocked`, or field absent → proceed.

### 3. Update status in file
In the YAML frontmatter block (between the first two `---` markers):
- If `status:` line exists: replace it with `status: closed`.
- If `status:` is absent: add `status: closed` as the last field before the closing `---`.

Use the Edit tool with the exact line content for precision.

### 4. Append completion note to the issue file
Append a new section to the end of the issue file's body:

```
## Abschluss (<YYYY-MM-DD>)

<note>
```

Where `<note>` is the completion note from `arguments`, or the issue `title` if none was provided. If the file already ends with an `## Abschluss (...)` section from a previous close (e.g. re-closed after being reopened), add a new dated section rather than overwriting the old one — it's a log, not a single field.

### 5. Report
```
Closed: 0021 — Materialise sibling sizes at group formation
  ✓ docs/issues/0021-materialise-sibling-sizes-at-group-formation.md  status → closed, Abschluss-Vermerk ergaenzt
```

## Done criterion

- Issue file: `status: closed` in frontmatter, plus a `## Abschluss (<date>)` section with the completion note in the body.
- No other file is read or modified — progress is not duplicated anywhere else.
