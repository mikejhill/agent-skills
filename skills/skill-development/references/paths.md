# Paths and temp files

## Locations

| Purpose | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Workspace scratch | `<workspace>\.tmp\<skill-name>\` | `<workspace>/.tmp/<skill-name>/` | same as macOS |
| System temp | `%TEMP%\agent-skills\<skill-name>\` | `$TMPDIR/agent-skills/<skill-name>/` | `${TMPDIR:-/tmp}/agent-skills/<skill-name>/` |
| Config | `%USERPROFILE%\.config\agent-skills\<skill-name>\` | `~/.config/agent-skills/<skill-name>/` | `${XDG_CONFIG_HOME:-~/.config}/agent-skills/<skill-name>/` |
| Cache and state | `%LOCALAPPDATA%\agent-skills\<skill-name>\` | `~/Library/Caches/agent-skills/<skill-name>/` | `${XDG_CACHE_HOME:-~/.cache}/agent-skills/<skill-name>/` |

Choose by lifetime and audience:

- **Workspace scratch** holds intermediate results, logs, and checkpoints for work in one project. Ensure `.tmp/` is gitignored before writing there.
- **System temp** holds output for the user with no project home, such as a handoff, an export, or a one-off report. The OS may delete it. On Unix, create the `agent-skills` and skill directories with mode `0700`, because `/tmp` is shared.
- **Config** holds settings and credentials the user creates. Scripts read it. Agents never write credentials. See the `skill-cli-development` skill.
- **Cache and state** holds data a script can rebuild, such as probe results, broker state, or downloads.

In Python:

```python
import os, sys, tempfile
from pathlib import Path

def system_temp(skill: str) -> Path:
    return Path(tempfile.gettempdir()) / "agent-skills" / skill

def user_cache(skill: str) -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
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
- Never fall back to the working directory when a system location is unusable. Stop and report.
- Leave temp files in place unless the skill states when to delete them. Report the path of anything the user needs.
- Give the user both the native path and a `file://` URI. If the agent runs remotely, say how to copy the file out.
