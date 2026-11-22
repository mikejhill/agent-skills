#!/usr/bin/env python3
"""Validate every skill with the Agent Skills reference validator (skills-ref).

Usage:
    python .github/ci/skills_ref_check.py [skills-root]

skills-ref allows only the spec frontmatter keys. This library also uses the
harness extension keys that skills/skill-development documents and checks
(EXTENSION_KEYS in check_skill.py), so those keys are removed before
validation. Every other skills-ref rule applies unchanged. Exits 1 on any
error, including a folder under the skills root with no SKILL.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

from skills_ref.errors import ParseError
from skills_ref.parser import find_skill_md, parse_frontmatter
from skills_ref.validator import validate_metadata

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills" / "skill-development" / "scripts"))
from check_skill import EXTENSION_KEYS  # noqa: E402


def check(skill_dir: Path) -> list[str]:
    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        return ["Missing required file: SKILL.md"]
    try:
        metadata, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ParseError as e:
        return [str(e)]
    for key in EXTENSION_KEYS:
        metadata.pop(key, None)
    return validate_metadata(metadata, skill_dir)


def main(argv: list[str]) -> int:
    root = Path(argv[0]) if argv else REPO / "skills"
    dirs = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not dirs:
        print(f"::error::no skill folders under {root}")
        return 1
    failed = 0
    for d in dirs:
        errors = check(d)
        if errors:
            failed += 1
            for err in errors:
                print(f"::error file={d.as_posix()}/SKILL.md::{d.name}: {err}")
        else:
            print(f"ok    {d.name}")
    print(f"{len(dirs)} skill(s) validated with skills-ref: {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
