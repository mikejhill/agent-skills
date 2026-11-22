#!/usr/bin/env python3
"""Check agent skill folders against the skill-development standards.

Usage:
    python3 check_skill.py <skill-dir-or-skills-root> [...] [--json]

A path that holds SKILL.md is checked as one skill; otherwise every direct
subfolder that holds SKILL.md is checked. Prints findings (human text, or
JSON with --json) and exits 1 if any error was found, else 0.
Stdlib only; Python 3.9+; Windows, macOS, and Linux.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
EXTENSION_KEYS = {"disable-model-invocation", "user-invocable", "argument-hint"}
# Words ending in "ing" that are not gerunds.
NOT_GERUNDS = {"string", "thing", "ring", "spring", "king", "wing", "ping", "bring", "sing", "swing"}
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")

SKILL_LINES_WARN = 200
SKILL_LINES_MAX = 500
DESC_WARN = 300
DESC_MAX = 1024


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    """Return (top-level keys -> raw scalar text, error) for a SKILL.md."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "SKILL.md does not start with '---' frontmatter"
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, "frontmatter has no closing '---'"
    fields: dict[str, str] = {}
    key = None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line[0].isspace():
            key, value = m.group(1), m.group(2).strip()
            if key in fields:
                return fields, f"duplicate frontmatter key '{key}'"
            fields[key] = "" if value in (">", ">-", "|", "|-") else value
        elif key is not None and line[0].isspace():
            fields[key] = (fields[key] + " " + line.strip()).strip()
        else:
            return fields, f"cannot parse frontmatter line: {line!r}"
    for k, v in fields.items():
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            fields[k] = v[1:-1]
    return fields, None


def strip_code(text: str) -> str:
    """Drop fenced code blocks and inline code so links inside them are ignored."""
    out, fence = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line.strip())
        if m:
            marker = m.group(1)[0] * 3
            if fence is None:
                fence = marker
            elif line.strip().startswith(fence):
                fence = None
            continue
        if fence is None:
            out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[dict[str, str]] = []

    def add(self, level: str, msg: str) -> None:
        self.findings.append({"skill": self.root.name, "level": level, "message": msg})

    def run(self) -> list[dict[str, str]]:
        skill_md = self.root / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        fields, err = parse_frontmatter(text)
        if err:
            self.add("error", err)
        self.check_name(fields.get("name", ""))
        self.check_description(fields.get("description", ""))
        self.check_keys(fields)
        n = len(text.splitlines())
        if n > SKILL_LINES_MAX:
            self.add("error", f"SKILL.md has {n} lines; the limit is {SKILL_LINES_MAX}")
        elif n > SKILL_LINES_WARN:
            self.add("warning", f"SKILL.md has {n} lines; aim for {SKILL_LINES_WARN} or fewer")
        for req in ("README.md", "INTENT.md"):
            if not (self.root / req).is_file():
                self.add("error", f"missing {req}")
        self.check_intent()
        self.check_layout()
        self.check_links()
        return self.findings

    def check_name(self, name: str) -> None:
        if not name:
            self.add("error", "frontmatter 'name' is missing")
            return
        if len(name) > 64 or not NAME_RE.match(name):
            self.add("error", f"name '{name}' must be 1-64 chars of a-z, 0-9 and single hyphens")
        if name != self.root.name:
            self.add("error", f"name '{name}' does not match folder '{self.root.name}'")
        gerunds = [w for w in name.split("-") if w.endswith("ing") and len(w) > 4 and w not in NOT_GERUNDS]
        if gerunds:
            self.add("warning", f"name uses a gerund ({', '.join(gerunds)}); prefer a noun phrase")

    def check_description(self, desc: str) -> None:
        if not desc:
            self.add("error", "frontmatter 'description' is missing or empty")
        elif len(desc) > DESC_MAX:
            self.add("error", f"description has {len(desc)} chars; the limit is {DESC_MAX}")
        elif len(desc) > DESC_WARN:
            self.add("warning", f"description has {len(desc)} chars; aim for {DESC_WARN} or fewer")

    def check_keys(self, fields: dict[str, str]) -> None:
        for k in fields:
            if k == "allowed-tools":
                self.add("warning", "'allowed-tools' is experimental and harness-specific")
            elif k not in SPEC_KEYS | EXTENSION_KEYS:
                self.add("warning", f"frontmatter key '{k}' is neither a spec field nor a known extension")
        if fields.get("disable-model-invocation") == "true" and fields.get("user-invocable") == "false":
            self.add("error", "both invocation paths are disabled; the skill is unreachable")
        if fields.get("disable-model-invocation") == "true":
            sidecar = self.root / "agents" / "openai.yaml"
            if not sidecar.is_file() or "allow_implicit_invocation: false" not in sidecar.read_text(encoding="utf-8"):
                self.add("warning", "user-only skill lacks agents/openai.yaml with allow_implicit_invocation: false")
        if "compatibility" in fields and len(fields["compatibility"]) > 500:
            self.add("error", "compatibility exceeds 500 chars")

    def check_intent(self) -> None:
        intent = self.root / "INTENT.md"
        if not intent.is_file():
            return
        text = intent.read_text(encoding="utf-8")
        for heading in ("## Goals", "## Requirements", "## Log"):
            if not re.search(rf"^{re.escape(heading)}\s*$", text, re.M):
                self.add("warning", f"INTENT.md has no '{heading}' section")

    def check_layout(self) -> None:
        refs = self.root / "references"
        if refs.is_dir():
            for p in refs.rglob("*"):
                if p.is_file() and p.parent != refs:
                    self.add("warning", f"{p.relative_to(self.root).as_posix()} is nested; keep references one level deep")

    def check_links(self) -> None:
        docs = [self.root / "SKILL.md", self.root / "README.md"]
        refs = self.root / "references"
        if refs.is_dir():
            docs += sorted(refs.glob("*.md"))
        for doc in docs:
            if not doc.is_file():
                continue
            for target in LINK_RE.findall(strip_code(doc.read_text(encoding="utf-8"))):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                path = target.split("#", 1)[0]
                if path.startswith("<") or "<" in path:
                    continue
                if not (doc.parent / path).exists():
                    self.add("error", f"{doc.relative_to(self.root).as_posix()}: broken link '{target}'")


def find_skills(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for p in paths:
        if (p / "SKILL.md").is_file():
            found.append(p)
        elif p.is_dir():
            found += sorted(d for d in p.iterdir() if (d / "SKILL.md").is_file())
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check agent skill folders against the skill-development standards.",
        epilog="example: python3 check_skill.py skills/my-skill",
    )
    ap.add_argument("paths", nargs="+", type=Path, help="skill folder(s) or a folder of skills")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    args = ap.parse_args(argv)

    skills = find_skills([p.resolve() for p in args.paths])
    if not skills:
        print("error: no folder with a SKILL.md found", file=sys.stderr)
        return 2
    findings = [f for s in skills for f in Checker(s).run()]
    errors = sum(f["level"] == "error" for f in findings)

    if args.json:
        print(json.dumps({"skills": len(skills), "errors": errors, "findings": findings}, indent=2))
    else:
        for f in findings:
            print(f"{f['level'].upper():7} {f['skill']}: {f['message']}")
        warnings = len(findings) - errors
        print(f"{len(skills)} skill(s) checked: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
