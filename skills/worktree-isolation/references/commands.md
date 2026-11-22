# Worktree commands

## Create: Bash (Linux, macOS, Git Bash)

```bash
purpose="agent-alpha"
repo_root="$(git rev-parse --show-toplevel)"
repo_name="$(basename "$repo_root")"
suffix="${purpose}-$(head -c3 /dev/urandom | od -An -tx1 | tr -d ' \n')"
branch="worktree/${suffix}"
wt_base="${XDG_DATA_HOME:-$HOME/.local/share}/agent-worktrees"
wt_path="${wt_base}/${repo_name}--${suffix}"
mkdir -p "$wt_base"
git worktree add "$wt_path" -b "$branch"
git worktree list
```

## Create: PowerShell

```powershell
$Purpose  = 'agent-alpha'
$RepoRoot = git rev-parse --show-toplevel
$RepoName = Split-Path $RepoRoot -Leaf
$Hex      = -join ((1..6) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 16) })
$Suffix   = "$Purpose-$Hex"
$Branch   = "worktree/$Suffix"
$DataHome = if ($env:XDG_DATA_HOME) { $env:XDG_DATA_HOME } else { Join-Path $HOME '.local/share' }
$WtBase   = Join-Path $DataHome 'agent-worktrees'
$WtPath   = Join-Path $WtBase "$RepoName--$Suffix"
New-Item -ItemType Directory -Force -Path $WtBase | Out-Null
git worktree add $WtPath -b $Branch
git worktree list
```

## Commit

```bash
git -C "$wt_path" add -A
git -C "$wt_path" commit -m "<type>(<scope>): <summary>"
```

## Apply

Run at most one of these, matching the strategy in `SKILL.md`. Never both. For speculative or experimental work, run neither: report the branch name only.

For a PR or review:

```bash
git push -u origin "$branch"
```

For a direct local merge:

```bash
git -C "$repo_root" merge --no-ff "$branch" -m "merge: <description>"
```

## Clean up

```bash
git worktree remove "$wt_path"     # add --force only for discarded work with uncommitted changes
git worktree prune
git branch -d "$branch"            # merged; use -D only for work the user discarded
```

On Windows, a process still running inside the worktree (an editor, a language server, a build daemon) locks the folder and makes `remove` fail. Stop it, then retry.
