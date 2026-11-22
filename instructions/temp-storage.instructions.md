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

Disposable working directories you create outside the current workspace go under one
scratch root, never in the user's project folders, home folder, or loose in the system
temp folder. Examples: a clone to review or test a branch, a verification or repro
directory, a build of another repository. Worktrees, caches, and persistent state such
as job directories keep their own locations and cleanup rules (see the
`worktree-isolation` and `skill-development` skills).

| OS | Scratch root |
| --- | --- |
| Windows | `%TEMP%\agent-skills\scratch\` (`%TEMP%` inside `%USERPROFILE%`) |
| macOS, Linux | `${TMPDIR:-/tmp}/agent-skills-<uid>/scratch/` (absolute `TMPDIR`; parent owned by you, mode `0700`, not a symlink) |

- One directory per use, named `<kind>-<YYYYMMDD-HHMMSS>-<slug>` in local time, for
  example `clone-20261122-185035-pr24-review` or `verify-20261122-191200-xh-fix`.
  `kind` is lowercase letters only.
- Before cloning a repository you already have locally, prefer a worktree of that
  clone. Clone into the scratch root only when no local clone exists. A review-only
  clone can be shallow or partial.
- Remove the directory when the task that created it ends, including when it fails.
  Reuse it across rounds of the same task, such as repeated reviews of one pull
  request, and remove it after the last round.
- Before removing it, check for anything still needed: uncommitted or unpushed changes
  (`git status --porcelain`, `git log @{u}..`), or a result with no other copy. Move
  those to where they belong, or keep the directory.
- To keep a directory (the user asked, it holds the only copy of something, or the task
  runs longer than 7 days), create an empty `KEEP` file in it and report its path. The
  sweep skips it. Remove `KEEP` when the reason ends.
- The session that asks for the directory owns its removal, on the machine where it
  lives. When another session or machine does the work, the brief names the path, and
  the last brief to a session on that machine asks it to remove the directory after it
  reports. Never write "leave it in place" without a later step that removes it.
- If removal fails because a file is locked or owned by another account (for example,
  files a sandboxed process created under its own account), report the path and move
  on. Don't escalate privileges to delete it.

### Sweep stale scratch

Before creating anything under the scratch root, remove its entries whose name
timestamp is more than 7 days old and that have no `KEEP` file. The sweep checks that
the root is the expected private directory and not a link, and touches nothing else.

```powershell
$base = [IO.Path]::GetFullPath($env:TEMP)
$parent = Join-Path $base 'agent-skills'; $root = Join-Path $parent 'scratch'
$rp = [IO.FileAttributes]::ReparsePoint
if ($base.StartsWith($env:USERPROFILE.TrimEnd('\') + '\', 'OrdinalIgnoreCase') -and
    (Test-Path -LiteralPath $root -PathType Container) -and
    -not ((Get-Item -LiteralPath $parent -Force).Attributes -band $rp) -and
    -not ((Get-Item -LiteralPath $root -Force).Attributes -band $rp)) {
  $cutoff = (Get-Date).AddDays(-7).ToString('yyyyMMdd')
  Get-ChildItem -LiteralPath $root -Directory -Force | Where-Object {
    -not ($_.Attributes -band $rp) -and $_.Name -match '^[a-z]+-(\d{8})-\d{6}(-|$)' -and
    $Matches[1] -lt $cutoff -and -not (Test-Path -LiteralPath (Join-Path $_.FullName 'KEEP'))
  } | Remove-Item -Recurse -Force -ErrorAction Continue
}
```

```sh
case "${TMPDIR:-}" in /*) base="$TMPDIR" ;; *) base=/tmp ;; esac
parent="${base%/}/agent-skills-$(id -u)"; root="$parent/scratch"
if [ -d "$root" ] && [ ! -L "$parent" ] && [ ! -L "$root" ] && [ -O "$parent" ] &&
   [ -O "$root" ] && [ "$(ls -ld "$parent" | cut -c5-10)" = "------" ]; then
  cutoff=$(date -d '7 days ago' +%Y%m%d 2>/dev/null || date -v-7d +%Y%m%d)
  for d in "$root"/*; do
    name=${d##*/}
    ts=$(printf '%s\n' "$name" | sed -n 's/^[a-z][a-z]*-\([0-9]\{8\}\)-[0-9]\{6\}\(-.*\)\{0,1\}$/\1/p')
    [ -n "$ts" ] && [ -d "$d" ] && [ ! -L "$d" ] && [ ! -e "$d/KEEP" ] &&
      [ "$ts" -lt "$cutoff" ] && rm -rf -- "$d"
  done
fi
```

## Naming files

Name ephemeral files `{kind}-{YYYYMMDD-HHMMSS}-{description}.{ext}` in local time,
for example `report-20261122-175433-auth-flow.md`. Never overwrite; on a clash append
`-2`, `-3`, and so on. Use plain names (`desc.ext`) only for files meant to persist
across sessions.
