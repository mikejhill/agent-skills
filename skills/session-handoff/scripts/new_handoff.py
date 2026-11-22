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
import errno
import json
import os
import re
import stat
import sys
from pathlib import Path

IS_WINDOWS = os.name == "nt"


FILE_ATTRIBUTE_REPARSE_POINT = 0x400
WRITE_FAILURES = {errno.EACCES, errno.EPERM, errno.EROFS, errno.ENOSPC, getattr(errno, "EDQUOT", errno.ENOSPC)}
MAX_SLUG = 60  # keeps names far below the 255-byte component limit


def _is_link_or_junction(path: Path) -> bool:
    """True for symlinks and, on Windows, any reparse point (junctions included)."""
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode):
        return True
    return bool(getattr(info, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


class Unusable(Exception):
    """The candidate root cannot be used; try the next one."""


def _candidate_roots() -> list[str]:
    names = ("TEMP", "TMP", "TMPDIR") if IS_WINDOWS else ("TMPDIR", "TEMP", "TMP")
    roots = [os.environ.get(name) or "" for name in names]
    if not IS_WINDOWS:
        roots += ["/tmp", "/var/tmp"]
    return roots


def _inside_user_profile(path: Path) -> bool:
    """Windows: the profile is ACL'd to its owner, so paths inside it are private."""
    profile = os.environ.get("USERPROFILE")
    if not profile:
        return False
    try:
        path.relative_to(Path(profile).resolve())
    except ValueError:
        return False
    return True


def _check_root(value: str) -> Path:
    """Validate a candidate temp root, raising Unusable if it does not qualify."""
    if not value:
        raise Unusable("unset")
    path = Path(value)
    if not path.is_absolute() or not path.is_dir():
        raise Unusable("not an absolute, existing directory")
    path = path.resolve()
    if IS_WINDOWS:
        if not _inside_user_profile(path):
            raise Unusable("outside %USERPROFILE%")
        return path
    info = os.stat(path)
    owned_private = info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o022
    sticky = bool(info.st_mode & stat.S_ISVTX) and info.st_uid in (0, os.getuid())
    if not (owned_private or sticky):
        raise Unusable("writable by others, and not sticky with a trusted owner")
    return path


def _handoff_dir(root: Path) -> Path:
    """Create or verify the private handoff directory inside a checked root.

    Raises Unusable when the root denies creation (try the next root) and
    SystemExit when an existing entry fails a privacy check (fail closed).
    """
    if IS_WINDOWS:
        directory = root / "agent-handoffs"
        try:
            directory.mkdir(exist_ok=True)
        except OSError as exc:
            if not _is_write_failure(exc):
                raise
            raise Unusable(f"cannot create {directory}: {exc}") from exc
        if _is_link_or_junction(directory) or not directory.is_dir():
            raise SystemExit(f"error: {directory} is a link, junction, or not a directory")
        return directory

    uid = os.getuid()
    directory = root / f"agent-handoffs-{uid}"
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as exc:
        if not _is_write_failure(exc):
            raise
        raise Unusable(f"cannot create {directory}: {exc}") from exc
    info = os.lstat(directory)
    if not stat.S_ISDIR(info.st_mode):
        raise SystemExit(f"error: {directory} exists and is not a plain directory")
    if info.st_uid != uid:
        raise SystemExit(f"error: {directory} is owned by uid {info.st_uid}, not {uid}")
    if stat.S_IMODE(info.st_mode) & 0o077:
        os.chmod(directory, 0o700)
    return directory


def _is_write_failure(exc: OSError) -> bool:
    """Errors that mean "this root cannot take a new file": try the next root."""
    return exc.errno in WRITE_FAILURES or isinstance(exc, PermissionError)


def reserve_handoff(slug: str) -> Path:
    """Reserve a file in the first usable private handoff directory. Never the cwd."""
    reasons = []
    for value in _candidate_roots():
        try:
            return reserve_file(_handoff_dir(_check_root(value)), slug)
        except Unusable as exc:
            reasons.append(f"{value or '(unset)'}: {exc}")
    raise SystemExit("error: no usable temp directory\n  " + "\n  ".join(reasons))


def slugify(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:5]
    slug = "-".join(words)[:MAX_SLUG].strip("-")
    return slug or "session"


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
        except OSError as exc:
            if not _is_write_failure(exc):
                raise
            raise Unusable(f"cannot create {path}: {exc}") from exc
        os.close(fd)
        return path
    raise Unusable(f"no free file name in {directory}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug", nargs="*", help="2-5 words naming the goal or focus")
    args = parser.parse_args()

    path = reserve_handoff(slugify(" ".join(args.slug)))
    json.dump({"path": str(path), "uri": path.as_uri()}, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
