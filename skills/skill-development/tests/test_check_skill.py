"""Tests for scripts/check_skill.py. Run: python3 -m unittest discover -s tests"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_skill  # noqa: E402

GOOD_INTENT = "# Intent\n\nX.\n\n## Goals\n\n1. A\n\n## Requirements\n\n- B\n\n## Log\n\n- 2026-01-01: C\n"


def make_skill(root: Path, name: str, front: str, body: str = "# T\n", files: dict[str, str] | None = None) -> Path:
    d = root / name
    d.mkdir()
    (d / "SKILL.md").write_text(f"---\n{front}---\n\n{body}", encoding="utf-8")
    defaults = {"README.md": "# r\n", "INTENT.md": GOOD_INTENT}
    for rel, text in {**defaults, **(files or {})}.items():
        if text is None:
            continue
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return d


def levels(d: Path) -> list[tuple[str, str]]:
    return [(f["level"], f["message"]) for f in check_skill.Checker(d).run()]


class CheckSkillTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_clean_skill_passes(self) -> None:
        d = make_skill(self.root, "good-skill", "name: good-skill\ndescription: >-\n  Does X. Use when Y.\n",
                       body="See [ref](references/a.md).\n", files={"references/a.md": "# a\n"})
        self.assertEqual(levels(d), [])

    def test_name_mismatch_and_gerund(self) -> None:
        d = make_skill(self.root, "writing-docs", "name: writing-doc\ndescription: Does X.\n")
        msgs = levels(d)
        self.assertTrue(any(l == "error" and "does not match folder" in m for l, m in msgs))
        self.assertTrue(any(l == "warning" and "gerund" in m for l, m in msgs))

    def test_missing_files_and_broken_link(self) -> None:
        d = make_skill(self.root, "s", "name: s\ndescription: Does X.\n", body="[x](references/nope.md)\n`[y](z.md)`\n",
                       files={"README.md": None, "INTENT.md": None})
        errors = [m for l, m in levels(d) if l == "error"]
        self.assertIn("missing README.md", errors)
        self.assertIn("missing INTENT.md", errors)
        self.assertEqual(sum("broken link" in m for m in errors), 1)

    def test_unreachable_and_sidecar(self) -> None:
        d = make_skill(self.root, "s", "name: s\ndescription: D.\ndisable-model-invocation: true\nuser-invocable: false\n")
        msgs = levels(d)
        self.assertTrue(any("unreachable" in m for _, m in msgs))
        self.assertTrue(any("openai.yaml" in m for _, m in msgs))

    def test_unknown_key_and_long_skill(self) -> None:
        d = make_skill(self.root, "s", "name: s\ndescription: D.\nmode: agent\n", body="line\n" * 600)
        msgs = levels(d)
        self.assertTrue(any(l == "warning" and "'mode'" in m for l, m in msgs))
        self.assertTrue(any(l == "error" and "limit is 500" in m for l, m in msgs))

    def test_main_exit_codes(self) -> None:
        make_skill(self.root, "ok", "name: ok\ndescription: D.\n")
        self.assertEqual(check_skill.main([str(self.root), "--json"]), 0)
        make_skill(self.root, "bad", "name: other\ndescription: D.\n")
        self.assertEqual(check_skill.main([str(self.root)]), 1)
        self.assertEqual(check_skill.main([str(self.root / "missing")]), 2)


if __name__ == "__main__":
    unittest.main()
