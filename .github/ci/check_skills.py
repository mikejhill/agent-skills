#!/usr/bin/env python3
"""Run both skill validators on every skill root: skills/ and harnesses/*/skills/.

Usage (from the repository root, same as CI):
    python .github/ci/check_skills.py

Runs skills-ref (skills_ref_check.py) and the agent-context checker
(check_skill.py) on each root, so harness-specific skills get the same checks
as root skills. Exits 1 if either validator fails on any root.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "skills" / "agent-context" / "scripts"))
import check_skill  # noqa: E402
import skills_ref_check  # noqa: E402


def skill_roots() -> list[Path]:
    roots = [REPO / "skills"]
    roots += sorted(p for p in (REPO / "harnesses").glob("*/skills") if p.is_dir())
    return roots


def main() -> int:
    failed = 0
    for root in skill_roots():
        print(f"== {root.relative_to(REPO).as_posix()}")
        failed |= skills_ref_check.main([str(root)])
        failed |= check_skill.main([str(root)])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
