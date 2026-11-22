#!/usr/bin/env python3
"""Reserve a new, private handoff file in the user's temp directory.

Prints JSON: {"path": <absolute native path>, "uri": <file:// URI>}.
The file is created empty, exclusively, and owner-only. Exits non-zero
without writing anywhere if no verified temp directory is usable.
Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import stat
import sys
from pathlib import Path

IS_WINDOWS = os.name == "nt"


def _usable_dir(value: str | None) -> Path | None:
    """Return the directory if it exists, is a directory, and is writable."""
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute() or not path.is_dir():
        return None
    if not os.access(path, os.W_OK | os.X_OK):
        return None
    return path.resolve()


def resolve_temp_dir() -> Path:
    """Pick the first verified temp directory. Never fall back to the cwd."""
    candidates = [os.environ.get(name) for name in ("TMPDIR", "TEMP", "TMP")]
    if not IS_WINDOWS:
        candidates += ["/tmp", "/var/tmp"]
    for candidate in candidates:
        found = _usable_dir(candidate)
        if found is not None:
            return found
    raise SystemExit("error: no existing, writable temp directory found (checked TMPDIR, TEMP, TMP"
                     + ("" if IS_WINDOWS else ", /tmp, /var/tmp") + ")")


def private_handoff_dir(temp: Path) -> Path:
    """Create or verify a per-user handoff directory only the user can access."""
    if IS_WINDOWS:
        # %TEMP% is already inside the user's profile and ACL'd to that user.
        directory = temp / "agent-handoffs"
        directory.mkdir(exist_ok=True)
        if directory.is_symlink() or not directory.is_dir():
            raise SystemExit(f"error: {directory} is not a plain directory")
        return directory

    uid = os.getuid()
    directory = temp / f"agent-handoffs-{uid}"
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = os.lstat(directory)
    if not stat.S_ISDIR(info.st_mode):
        raise SystemExit(f"error: {directory} exists and is not a plain directory")
    if info.st_uid != uid:
        raise SystemExit(f"error: {directory} is owned by uid {info.st_uid}, not {uid}")
    if stat.S_IMODE(info.st_mode) & 0o077:
        os.chmod(directory, 0o700)
    return directory


def slugify(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:5]
    return "-".join(words) or "session"


def reserve_file(directory: Path, slug: str) -> Path:
    """Create the file exclusively; on a name clash, try the next suffix."""
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"handoff-{stamp}-{slug}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    for attempt in range(1, 1000):
        name = f"{base}.md" if attempt == 1 else f"{base}-{attempt}.md"
        path = directory / name
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError:
            continue
        os.close(fd)
        return path
    raise SystemExit(f"error: could not reserve a unique file name in {directory}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug", nargs="*", help="2-5 words naming the goal or focus")
    args = parser.parse_args()

    path = reserve_file(private_handoff_dir(resolve_temp_dir()), slugify(" ".join(args.slug)))
    json.dump({"path": str(path), "uri": path.as_uri()}, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
