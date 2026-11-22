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
- Before removing it, check for anything still needed: uncommitted changes
  (`git status --porcelain`), commits on no remote
  (`git log HEAD --branches --not --remotes --oneline`), or a result with no other
  copy. Move those to where they belong, or keep the directory. If a check fails, keep
  it.
- To keep a directory (the user asked, it holds the only copy of something, or the task
  runs longer than 7 days), create an empty `KEEP` file in it and report its path. The
  sweep skips it. Remove `KEEP` when the reason ends.
- The session that asks for the directory owns its removal, on the machine where it
  lives. When another session or machine does the work, the brief names the path, and
  the last brief to a session on that machine asks it to remove the directory after it
  reports. Never write "leave it in place" without a later step that removes it.
- If removal fails because a file is locked or owned by another account (for example,
  files a sandboxed process created under its own account), report the path and stop
  there. Don't escalate privileges to delete it; the user can.

### Create the root and sweep stale scratch

Before creating anything under the scratch root, run the block for your OS. It creates
the root if missing (private on Unix), stops with a warning if the path contains a link
or has unsafe ownership, and removes entries whose name timestamp is more than 7 days
old, unless they have a `KEEP` file or a Git checkout with unsaved work. Kept entries
are reported. It touches nothing outside the root.

```powershell
& {
  $prof = [IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd('\')
  $base = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')
  $root = Join-Path $base 'agent-skills\scratch'
  $rp = [IO.FileAttributes]::ReparsePoint
  $linked = {
    for ($p = $root; $p.Length -gt $prof.Length; $p = Split-Path $p -Parent) {
      if ((Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p -Force).Attributes -band $rp)) { return $p }
    }
  }
  if (-not $base.StartsWith($prof + '\', 'OrdinalIgnoreCase')) { Write-Warning "TEMP is outside the profile: $base"; return }
  if ($l = & $linked) { Write-Warning "link in scratch path: $l"; return }
  New-Item -ItemType Directory -Force -Path $root | Out-Null
  if ($l = & $linked) { Write-Warning "link in scratch path: $l"; return }
  $cutoff = (Get-Date).AddDays(-7).ToString('yyyyMMddHHmmss')
  foreach ($d in Get-ChildItem -LiteralPath $root -Directory -Force) {
    if (($d.Attributes -band $rp) -or ($d.Name -notmatch '^[a-z]+-(\d{8})-(\d{6})(-|$)') -or
        (($Matches[1] + $Matches[2]) -ge $cutoff) -or (Test-Path -LiteralPath (Join-Path $d.FullName 'KEEP'))) { continue }
    if (Test-Path -LiteralPath (Join-Path $d.FullName '.git')) {
      $s = git -C $d.FullName status --porcelain 2>&1; $ok = $LASTEXITCODE -eq 0
      $c = git -C $d.FullName log HEAD --branches --not --remotes --oneline 2>&1; $ok = $ok -and $LASTEXITCODE -eq 0
      if (-not $ok -or $s -or $c) { Write-Warning "kept, unsaved work or unreadable: $($d.FullName)"; continue }
    }
    Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction Continue
  }
}
```

```sh
(
  case "${TMPDIR:-}" in /*) base="$TMPDIR" ;; *) base=/tmp ;; esac
  parent="${base%/}/agent-skills-$(id -u)"; root="$parent/scratch"
  unsafe() { [ -L "$1" ] || [ ! -d "$1" ] || [ ! -O "$1" ] || [ "$(ls -ld "$1" | cut -c5-10)" != "------" ]; }
  if [ -e "$parent" ] || [ -L "$parent" ]; then unsafe "$parent" && { echo "unsafe: $parent" >&2; exit 1; }; fi
  (umask 077; mkdir -p "$root") || exit 1
  unsafe "$parent" || unsafe "$root" && { echo "unsafe: $root" >&2; exit 1; }
  cutoff=$(date -d '7 days ago' +%Y%m%d%H%M%S 2>/dev/null || date -v-7d +%Y%m%d%H%M%S)
  for d in "$root"/*; do
    ts=$(printf '%s\n' "${d##*/}" | sed -n 's/^[a-z][a-z]*-\([0-9]\{8\}\)-\([0-9]\{6\}\)\(-.*\)\{0,1\}$/\1\2/p')
    [ -n "$ts" ] && [ -d "$d" ] && [ ! -L "$d" ] && [ ! -e "$d/KEEP" ] && [ "$ts" -lt "$cutoff" ] || continue
    if [ -e "$d/.git" ]; then
      s=$(git -C "$d" status --porcelain 2>&1) && c=$(git -C "$d" log HEAD --branches --not --remotes --oneline 2>&1) &&
        [ -z "$s$c" ] || { echo "kept, unsaved work or unreadable: $d" >&2; continue; }
    fi
    rm -rf -- "$d"
  done
)
```

## Naming files

Name ephemeral files `{kind}-{YYYYMMDD-HHMMSS}-{description}.{ext}` in local time,
for example `report-20261122-175433-auth-flow.md`. Never overwrite; on a clash append
`-2`, `-3`, and so on. Use plain names (`desc.ext`) only for files meant to persist
across sessions.
