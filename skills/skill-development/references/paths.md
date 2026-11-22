# Paths and temp files

## Locations

| Purpose | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Workspace scratch | `<workspace>\.tmp\<skill-name>\` | `<workspace>/.tmp/<skill-name>/` | same as macOS |
| System temp | `%TEMP%\agent-skills\<skill-name>\` | `$TMPDIR/agent-skills-<uid>/<skill-name>/` | `${TMPDIR:-/tmp}/agent-skills-<uid>/<skill-name>/` |
| Agent scratch | `%TEMP%\agent-skills\scratch\` | `$TMPDIR/agent-skills-<uid>/scratch/` | `${TMPDIR:-/tmp}/agent-skills-<uid>/scratch/` |
| Config | `%XDG_CONFIG_HOME%` or `%USERPROFILE%\.config`, then `\agent-skills\<skill-name>\` | `${XDG_CONFIG_HOME:-~/.config}/agent-skills/<skill-name>/` | same as macOS |
| Cache and state | `%LOCALAPPDATA%\agent-skills\<skill-name>\` | `~/Library/Caches/agent-skills/<skill-name>/` | `${XDG_CACHE_HOME:-~/.cache}/agent-skills/<skill-name>/` |

Choose by lifetime and audience:

- **Workspace scratch** holds intermediate results, logs, and checkpoints for work in one project. Ensure `.tmp/` is gitignored before writing there.
- **System temp** holds output for the user with no project home, such as a handoff, an export, or a one-off report. The OS may delete it. On Unix the parent is per user (`agent-skills-<uid>`, from `id -u`), because `/tmp` is shared: create it with mode `0700`, and before reuse verify it is a real directory (not a symlink), owned by you, and grants no group or other access (mode `0700`). Otherwise stop.
- **Agent scratch** holds working directories outside any workspace, such as a clone to review a branch or a verification directory. One directory per use, named `<kind>-<YYYYMMDD-HHMMSS>-<slug>`, removed when the task ends. Worktrees, caches, and job state are not scratch. If the user's instructions define more for this root, such as retention markers or a sweep of stale entries, follow them.
- **Config** honors `XDG_CONFIG_HOME` on every OS. It holds settings and credentials the user creates. Scripts read it. Agents never write credentials. See [cli.md](cli.md).
- **Cache and state** holds data a script can rebuild, such as probe results, broker state, or downloads.

System temp root, chosen explicitly. Do not use `tempfile.gettempdir()`, because it falls back to the working directory:

- Candidates: Windows `TEMP`, then `TMP`. Unix `TMPDIR`, then `/tmp`, then `/var/tmp`. Skip relative, missing, or unwritable roots.
- A root must be private before user-facing files go under it. On Windows it must sit inside `%USERPROFILE%`, whose ACL is owner-only. On Unix it must be owned by you and not group- or other-writable, or be sticky and owned by you or `root`, like `/tmp`.
- If no root qualifies, stop and report.

Cache root in Python:

```python
import os, sys
from pathlib import Path

def env_root(var: str, default: Path) -> Path:
    value = os.environ.get(var, "")
    return Path(value) if value and Path(value).is_absolute() else default  # ignore relative values

def user_cache(skill: str) -> Path:
    if sys.platform == "win32":
        base = env_root("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = env_root("XDG_CACHE_HOME", Path.home() / ".cache")
    return base / "agent-skills" / skill
```

## File names

`<kind>-<YYYYMMDD-HHMMSS>[-<slug>].<ext>`

- `kind`: one lowercase noun for what the file is, such as `report`, `log`, `handoff`, `screenshot`, or `checkpoint`.
- Timestamp: local time, captured when the file is created.
- `slug`: optional. Two to five lowercase-kebab words, 60 characters at most, saying what it is about.
- Examples: `log-20261122-093015.txt` and `handoff-20261122-175433-fix-safari-export.md`.

## Rules

- Create directories on first write, not on first run.
- Create files exclusively, with `open(path, "x")` or `New-Item`, which fails if the file exists. On a name clash, append `-2`, `-3`, and so on. Never overwrite.
- Never write into the skill folder at run time. It may be read-only or synced, and changes there are lost or leak into every installation.
- Never fall back to the working directory when a system location is unusable. Stop and report. Ignore relative values in `TMPDIR`, `XDG_*`, or `LOCALAPPDATA`.
- State when each temp file or directory is removed. Remove working directories (clones, builds, verification or repro directories) when the run ends, also on failure. Leave output meant for the user in place and report its path.
- Give the user both the native path and a `file://` URI. If the agent runs remotely, say how to copy the file out.
