# Git Workflow

## Commit Message Format
```
<type>: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci

Note: Attribution disabled globally via ~/.claude/settings.json.

## Pull Request Workflow

When creating PRs:
1. Analyze full commit history (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch

> For the full development process (planning, TDD, code review) before git operations,
> see [development-workflow.md](./development-workflow.md).

## Worktrees: Only on Explicit Request

Do not create a git worktree unless the user explicitly asks for one. When a user says
"in a separate/own branch" without saying "worktree", that means a branch in the main
checkout (`git checkout -b <name>`), not a worktree — the choice between the two belongs
to the user, not to a default assumption.

Worktrees put the result in a directory the user isn't working in, which then has to be
merged or extracted back out — useful for AFK/multi-agent fan-out, unwanted overhead for
an interactive session. If a worktree turns out to be wanted after the fact, use the
project's dedicated worktree-creation tooling if one exists, rather than a raw
`git worktree add`, so the new worktree gets the same local project context (skills,
settings, docs) as the main checkout. When genuinely unsure which the user wants, ask
instead of deciding.
