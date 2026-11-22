---
name: agent-tmp-directory
description: Where agents put temporary files, clones, and scratch work, how to name them, and when to remove them.
applyTo: "**"
---

# Agent Temporary Files

## Workspace scratch: `.tmp/`

Store ephemeral files for the current project in `.tmp/`. Use it liberally for
state preservation, rollback, debugging, and inter-agent coordination.

```text
.tmp/
  checkpoints/   # State before risky operations
  scripts/       # Generated scripts
  outputs/       # Tool call outputs
  reports/       # Analyses and reports
  info/          # Inferred/cached information
```

Skills put their workspace scratch in `.tmp/<skill-name>/`. Output meant for the user with no project home, such as a handoff, follows that skill's own destination.

- Never commit `.tmp/`. It must be in `.gitignore`.
- Keep `.tmp/` files for debugging and rollback. Delete them only when they would make state inaccurate.
- Avoid disrupting files in use by other agents.

## Scratch outside the workspace

Anything you create outside the current workspace for your own use goes under one
root, never in the user's project folders, home folder, or loose in the system temp
folder. Examples: a clone to review or test a branch, a verification or repro
directory, a build of another repository.

| OS | Scratch root |
| --- | --- |
| Windows | `%TEMP%\agent-skills\scratch\` |
| macOS, Linux | `${TMPDIR:-/tmp}/agent-skills-<uid>/scratch/` (parent mode `0700`) |

- One directory per use, named `<kind>-<YYYYMMDD-HHMMSS>-<slug>` in local time, for
  example `clone-20261122-185035-pr24-review` or `verify-20261122-191200-xh-fix`.
- Before cloning a repository you already have locally, prefer a worktree of that
  clone (see the `worktree-isolation` skill). Clone into the scratch root only when
  no local clone exists. A review-only clone can be shallow or partial.
- Remove the directory when the task that created it ends, including when it fails.
  Reuse it across rounds of the same task, such as repeated reviews of one pull
  request, and remove it after the last round.
- Keep it only when the user asks to, or when it holds the only copy of a result.
  Then report its path.
- When you hand work to another session or machine, put the scratch path in the brief,
  and in the brief for the last round, ask it to remove the directory. Never write
  "leave it in place" without a later step that removes it.
- If removal fails because a file is locked or owned by another account (for example,
  a folder created inside a Codex sandbox on Windows), report the path and move on.
  Don't escalate privileges to delete it.

### Sweep stale scratch

Before creating anything under the scratch root, remove its entries more than 7 days
old. Touch nothing outside the root.

```powershell
$root = Join-Path $env:TEMP 'agent-skills\scratch'
if (Test-Path $root) {
  Get-ChildItem $root -Directory | Where-Object LastWriteTime -lt (Get-Date).AddDays(-7) |
    Remove-Item -Recurse -Force -ErrorAction Continue
}
```

```sh
root="${TMPDIR:-/tmp}/agent-skills-$(id -u)/scratch"
[ -d "$root" ] && find "$root" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

## Naming files

Name ephemeral files `{kind}-{YYYYMMDD-HHMMSS}-{description}.{ext}` in local time,
for example `report-20261122-175433-auth-flow.md`. Never overwrite; on a clash append
`-2`, `-3`, and so on. Use plain names (`desc.ext`) only for files meant to persist
across sessions.
