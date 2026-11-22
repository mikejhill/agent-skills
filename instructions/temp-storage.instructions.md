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
  clone can be shallow or partial. Fetch a pull request head into a remote-tracking
  ref (`git fetch origin pull/<n>/head:refs/remotes/origin/pr/<n>`), not only
  `FETCH_HEAD`, so later checks see it as already on a remote.
- Remove the directory when the task that created it ends, including when it fails.
  Reuse it across rounds of the same task, such as repeated reviews of one pull
  request, and remove it after the last round.
- Before removing it, check each Git checkout in it for work with no other copy:
  `git status --porcelain --untracked-files=all` (uncommitted or new files),
  `git stash list` (stashes), and `git log HEAD --branches --not --remotes --oneline`
  (commits on no remote). Any output means move that work to where it belongs, or keep
  the directory. Also keep it if a check fails or it holds a result with no other copy.
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

Before creating anything under the scratch root, run the block for your OS, and don't
create anything if it fails. It validates the temp base, creates the root if missing
(private on Unix), and fails on a link or unsafe ownership along the path. It then
removes entries whose name timestamp is more than 7 days old, except entries with a
`KEEP` file, a Git checkout with unsaved work (the checks above), a Git checkout below
the top level, or a check that fails. It reports each kept entry and the reason, and
touches nothing outside the root.

```powershell
& {
  $ErrorActionPreference = 'Stop'
  $prof = [IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd('\')
  $base = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')
  $root = Join-Path $base 'agent-skills\scratch'
  $rp = [IO.FileAttributes]::ReparsePoint
  $assertNoLinks = {
    for ($p = $root; $p.Length -gt $prof.Length; $p = Split-Path $p -Parent) {
      if ((Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p -Force).Attributes -band $rp)) { throw "link in scratch path: $p" }
    }
  }
  if (-not $base.StartsWith($prof + '\', 'OrdinalIgnoreCase')) { throw "TEMP is outside the profile: $base" }
  & $assertNoLinks
  New-Item -ItemType Directory -Force -Path $root | Out-Null
  & $assertNoLinks
  $unsaved = {
    param($repo)
    $ErrorActionPreference = 'Continue'  # Git writes warnings to stderr
    $out = @()
    foreach ($cmd in @(@('status', '--porcelain', '--untracked-files=all'), @('stash', 'list'),
                       @('log', 'HEAD', '--branches', '--not', '--remotes', '--oneline'))) {
      $out += git -C $repo @cmd 2>&1
      if ($LASTEXITCODE -ne 0) { return 'a Git check failed' }
    }
    if ($out) { return 'unsaved Git work' }
  }
  $cutoff = (Get-Date).AddDays(-7).ToString('yyyyMMddHHmmss')
  foreach ($d in Get-ChildItem -LiteralPath $root -Directory -Force) {
    if (($d.Attributes -band $rp) -or ($d.Name -notmatch '^[a-z]+-(\d{8})-(\d{6})(-|$)') -or
        (($Matches[1] + $Matches[2]) -ge $cutoff) -or (Test-Path -LiteralPath (Join-Path $d.FullName 'KEEP'))) { continue }
    $why = $null
    $nested = Get-ChildItem -LiteralPath $d.FullName -Recurse -Force -Filter '.git' -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -ne (Join-Path $d.FullName '.git') }
    if ($nested) { $why = 'a Git checkout below the top level' }
    elseif (Test-Path -LiteralPath (Join-Path $d.FullName '.git')) { $why = & $unsaved $d.FullName }
    if ($why) { Write-Warning "kept ($why): $($d.FullName)"; continue }
    Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction Continue
  }
}
```

```sh
(
  set -u
  case "${TMPDIR:-}" in /*) base="${TMPDIR%/}" ;; *) base=/tmp ;; esac
  parent="$base/agent-skills-$(id -u)"; root="$parent/scratch"
  mode() { ls -ldn "$1" | cut -c1-10; }
  owner() { ls -ldn "$1" | awk '{print $3}'; }
  # Base: yours or root's, and either not writable by others or sticky (like /tmp).
  [ -d "$base" ] && [ ! -L "$base" ] || { echo "unsafe temp base: $base" >&2; exit 1; }
  case "$(owner "$base")" in 0|"$(id -u)") ;; *) echo "unsafe temp base: $base" >&2; exit 1 ;; esac
  case "$(mode "$base")" in ?????w????|????????w?) case "$(mode "$base")" in *t|*T) ;; *) echo "unsafe temp base: $base" >&2; exit 1 ;; esac ;; esac
  unsafe() { [ -L "$1" ] || [ ! -d "$1" ] || [ "$(owner "$1")" != "$(id -u)" ] || [ "$(mode "$1" | cut -c5-10)" != "------" ]; }
  if [ -e "$parent" ] || [ -L "$parent" ]; then unsafe "$parent" && { echo "unsafe: $parent" >&2; exit 1; }; fi
  (umask 077; mkdir -p "$root") || exit 1
  if unsafe "$parent" || unsafe "$root"; then echo "unsafe: $root" >&2; exit 1; fi
  unsaved() {
    out=$(git -C "$1" status --porcelain --untracked-files=all 2>&1 &&
          git -C "$1" stash list 2>&1 &&
          git -C "$1" log HEAD --branches --not --remotes --oneline 2>&1) || { echo "a Git check failed"; return; }
    [ -z "$out" ] || echo "unsaved Git work"
  }
  cutoff=$(date -d '7 days ago' +%Y%m%d%H%M%S 2>/dev/null || date -v-7d +%Y%m%d%H%M%S)
  for d in "$root"/*; do
    ts=$(printf '%s\n' "${d##*/}" | sed -n 's/^[a-z][a-z]*-\([0-9]\{8\}\)-\([0-9]\{6\}\)\(-.*\)\{0,1\}$/\1\2/p')
    [ -n "$ts" ] && [ -d "$d" ] && [ ! -L "$d" ] && [ ! -e "$d/KEEP" ] && [ "$ts" -lt "$cutoff" ] || continue
    why=""
    if [ -n "$(find "$d" -mindepth 2 -name .git -print -quit 2>/dev/null)" ]; then why="a Git checkout below the top level"
    elif [ -e "$d/.git" ]; then why=$(unsaved "$d"); fi
    if [ -n "$why" ]; then echo "kept ($why): $d" >&2; else rm -rf -- "$d"; fi
  done
)
```

## Naming files

Name ephemeral files `{kind}-{YYYYMMDD-HHMMSS}-{description}.{ext}` in local time,
for example `report-20261122-175433-auth-flow.md`. Never overwrite; on a clash append
`-2`, `-3`, and so on. Use plain names (`desc.ext`) only for files meant to persist
across sessions.
