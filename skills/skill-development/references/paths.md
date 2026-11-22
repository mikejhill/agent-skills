# Paths and temp files

## Locations

| Purpose | Windows | macOS | Linux |
| --- | --- | --- | --- |
| Workspace scratch | `<workspace>\.tmp\<skill-name>\` | `<workspace>/.tmp/<skill-name>/` | same as macOS |
| System temp | `%TEMP%\agent-skills\<skill-name>\` | `$TMPDIR/agent-skills-<uid>/<skill-name>/` | `${TMPDIR:-/tmp}/agent-skills-<uid>/<skill-name>/` |
| Config | `%XDG_CONFIG_HOME%` or `%USERPROFILE%\.config`, then `\agent-skills\<skill-name>\` | `${XDG_CONFIG_HOME:-~/.config}/agent-skills/<skill-name>/` | same as macOS |
| Cache and state | `%LOCALAPPDATA%\agent-skills\<skill-name>\` | `~/Library/Caches/agent-skills/<skill-name>/` | `${XDG_CACHE_HOME:-~/.cache}/agent-skills/<skill-name>/` |

Choose by lifetime and audience:

- **Workspace scratch** holds intermediate results, logs, and checkpoints for work in one project. Ensure `.tmp/` is gitignored before writing there.
- **System temp** holds output for the user with no project home, such as a handoff, an export, or a one-off report. The OS may delete it. On Unix the parent is per user (`agent-skills-<uid>`, from `id -u`), because `/tmp` is shared: create it with mode `0700`, and before reuse verify it is a real directory (not a symlink), owned by you, and not group- or world-writable. Otherwise stop.
- **Config** honors `XDG_CONFIG_HOME` on every OS, matching `skill-cli-development`. It holds settings and credentials the user creates. Scripts read it. Agents never write credentials. See the `skill-cli-development` skill.
- **Cache and state** holds data a script can rebuild, such as probe results, broker state, or downloads.

In Python. Do not use `tempfile.gettempdir()`, because it falls back to the working directory:

```python
import os, stat, sys
from pathlib import Path

def system_temp(skill: str) -> Path:
    if sys.platform == "win32":
        roots = [os.environ.get(v) for v in ("TEMP", "TMP")]
    else:
        roots = [os.environ.get("TMPDIR"), "/tmp", "/var/tmp"]
    for root in filter(None, roots):
        base = Path(root)
        if not (base.is_absolute() and base.is_dir() and os.access(base, os.W_OK | os.X_OK)):
            continue
        if sys.platform == "win32":
            return base / "agent-skills" / skill
        parent = base / f"agent-skills-{os.getuid()}"
        parent.mkdir(mode=0o700, exist_ok=True)
        st = parent.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o022:
            raise SystemExit(f"unsafe temp directory: {parent}")
        return parent / skill
    raise SystemExit("no usable system temp directory")

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
