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
import subprocess
import sys
from pathlib import Path

IS_WINDOWS = os.name == "nt"


FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def _is_link_or_junction(path: Path) -> bool:
    """True for symlinks and, on Windows, any reparse point (junctions included)."""
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode):
        return True
    return bool(getattr(info, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def _usable_dir(value: str | None) -> Path | None:
    """Return the directory if it is absolute, exists, and is writable."""
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute() or not path.is_dir():
        return None
    if not os.access(path, os.W_OK | os.X_OK):
        return None
    path = path.resolve()
    if IS_WINDOWS and not _inside_user_profile(path):
        return None
    return path


def _inside_user_profile(path: Path) -> bool:
    """Windows: accept only temp roots inside the user's own profile."""
    profile = os.environ.get("USERPROFILE")
    if not profile:
        return False
    try:
        path.relative_to(Path(profile).resolve())
    except ValueError:
        return False
    return True


def resolve_temp_dir() -> Path:
    """Pick the first verified temp directory. Never fall back to the cwd."""
    names = ("TEMP", "TMP", "TMPDIR") if IS_WINDOWS else ("TMPDIR", "TEMP", "TMP")
    candidates = [os.environ.get(name) for name in names]
    if not IS_WINDOWS:
        candidates += ["/tmp", "/var/tmp"]
    for candidate in candidates:
        found = _usable_dir(candidate)
        if found is not None:
            return found
    where = "inside %USERPROFILE%" if IS_WINDOWS else "(also checked /tmp, /var/tmp)"
    raise SystemExit(f"error: no absolute, existing, writable temp directory in {', '.join(names)} {where}")


def _restrict_windows_acl(directory: Path) -> None:
    """Remove inherited ACEs and grant full control to the current user only."""
    user = os.environ.get("USERNAME")
    domain = os.environ.get("USERDOMAIN")
    if not user:
        raise SystemExit("error: USERNAME is not set; cannot restrict the handoff directory")
    principal = f"{domain}\\{user}" if domain else user
    result = subprocess.run(
        ["icacls", str(directory), "/inheritance:r", "/grant:r", f"{principal}:(OI)(CI)F"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"error: could not restrict {directory} to {principal}: "
                         f"{(result.stderr or result.stdout).strip()}")


def private_handoff_dir(temp: Path) -> Path:
    """Create or verify a per-user handoff directory only the user can access."""
    if IS_WINDOWS:
        directory = temp / "agent-handoffs"
        directory.mkdir(exist_ok=True)
        if _is_link_or_junction(directory) or not directory.is_dir():
            raise SystemExit(f"error: {directory} is a link, junction, or not a directory")
        _restrict_windows_acl(directory)
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
    for attempt in range(1, 100):
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
