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
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")

SKILL_LINES_WARN = 200
SKILL_LINES_MAX = 500
DESC_WARN = 300
DESC_MAX = 1024


STRING_KEYS = ("name", "description", "license", "compatibility", "argument-hint")
BOOL_KEYS = ("disable-model-invocation", "user-invocable")


def split_frontmatter(text: str) -> tuple[str | None, str | None]:
    """Return (frontmatter source, error) for a SKILL.md."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "SKILL.md does not start with '---' frontmatter"
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return "\n".join(lines[1:i]), None
    return None, "frontmatter has no closing '---'"


def _plain_scalar(raw: str) -> tuple[object, str | None]:
    """Interpret one single-line YAML scalar the way a YAML loader would."""
    if raw[:1] == '"' and "\\" in raw:
        return None, "uses a backslash escape; use single quotes or a '>-' block"
    if raw[:1] in ("'", '"'):
        q = raw[0]
        close = raw.find(q, 1)
        while q == "'" and close != -1 and raw[close + 1:close + 2] == "'":
            close = raw.find(q, close + 2)
        if close == -1:
            return None, "unterminated quoted string"
        rest = raw[close + 1:].strip()
        if rest and not rest.startswith("#"):
            return None, "text after a quoted string"
        body = raw[1:close]
        return (body.replace("''", "'") if q == "'" else body), None
    if raw.startswith("#"):
        return None, None  # comment only: YAML reads null
    if raw.startswith("- ") or raw == "-":
        return None, "is a YAML sequence item, not a string"
    value = re.split(r"\s#", raw, maxsplit=1)[0].strip()
    if value[:1] in ("[", "{"):
        return value, "is a YAML collection, not a string"
    if value[:1] in ("&", "*", "!", "%", "@", "`", "|", ">"):
        return None, f"starts with the YAML indicator '{value[0]}'"
    if ": " in value or value.endswith(":"):
        return None, "contains ': ' (quote it or use a '>-' block)"
    if value in ("true", "false"):
        return value == "true", None
    if value in ("", "~", "null", "Null", "NULL"):
        return None, None
    if re.fullmatch(r"[-+]?(\d[\d_]*(\.\d*)?|\.\d+)([eE][-+]?\d+)?|0x[0-9a-fA-F]+|0o[0-7]+|[-+]?\.(inf|Inf)|\.(nan|NaN)", value):
        return 0, None  # a number, never a string
    if value.lower() in ("yes", "no", "on", "off", "y", "n", "true", "false", "null"):
        return None, f"is the ambiguous YAML word '{value}'; quote it or use true/false"
    if re.match(r"^\d{4}-\d\d?-\d\d?([Tt ]|$)", value):
        return None, f"looks like a YAML date ('{value}'); quote it"
    return value, None


def parse_frontmatter_subset(src: str) -> tuple[dict[str, object], str | None]:
    """Strict parser for the YAML subset skills use, when PyYAML is absent."""
    fields: dict[str, object] = {}
    lines = src.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s+(.*))?$", line)
        if not m:
            return fields, f"cannot parse frontmatter line: {line!r}"
        key, raw = m.group(1), (m.group(2) or "").strip()
        if key in fields:
            return fields, f"duplicate frontmatter key '{key}'"
        block: list[str] = []
        while i < len(lines) and (not lines[i].strip() or lines[i][0].isspace()):
            block.append(lines[i])
            i += 1
        filled = [b for b in block if b.strip()]
        indents = {len(b) - len(b.lstrip()) for b in filled}
        if re.match(r"^[>|][+-]?(\s+#.*)?$", raw):
            if filled and min(indents) != len(filled[0]) - len(filled[0].lstrip()):
                return fields, f"'{key}' block is less indented after its first line"
            parts = [b.strip() for b in block]
            fields[key] = (" " if raw[0] == ">" else "\n").join(p for p in parts if p)
        elif raw:
            if any(b.strip() for b in block):
                return fields, f"'{key}' has a value and indented lines"
            value, err = _plain_scalar(raw)
            if err:
                return fields, f"'{key}' {err}"
            fields[key] = value
        else:
            sub: dict[str, object] = {}
            if len({len(b) - len(b.lstrip()) for b in filled if not b.lstrip().startswith("#")}) > 1:
                return fields, f"'{key}' entries are not evenly indented (only one level is supported)"
            for b in block:
                if not b.strip() or b.lstrip().startswith("#"):
                    continue
                sm = re.match(r"^\s+([A-Za-z][A-Za-z0-9_.-]*):\s+(.*)$", b)
                if not sm:
                    return fields, f"cannot parse frontmatter line: {b!r}"
                value, err = _plain_scalar(sm.group(2).strip())
                if err:
                    return fields, f"'{key}.{sm.group(1)}' {err}"
                if sm.group(1) in sub:
                    return fields, f"duplicate key '{key}.{sm.group(1)}'"
                sub[sm.group(1)] = value
            fields[key] = sub
    return fields, None


def parse_frontmatter(text: str) -> tuple[dict[str, object], str | None]:
    """Return (frontmatter fields, error).

    Deliberately accepts only a strict YAML subset (plain or quoted scalars,
    block scalars, one-level maps) so the verdict is the same everywhere and
    anything a YAML loader could read differently is rejected.
    """
    src, err = split_frontmatter(text)
    if err or src is None:
        return {}, err
    return parse_frontmatter_subset(src)


def type_errors(fields: dict[str, object]) -> list[str]:
    errs = [f"'{k}' must be a string" for k in STRING_KEYS if k in fields and not isinstance(fields[k], str)]
    errs += [f"'{k}' must be true or false" for k in BOOL_KEYS if k in fields and not isinstance(fields[k], bool)]
    meta = fields.get("metadata", {})
    if not (isinstance(meta, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in meta.items())):
        errs.append("'metadata' must map keys to string values")
    return errs


def sidecar_disables_implicit(text: str) -> bool:
    """True if agents/openai.yaml sets policy.allow_implicit_invocation: false as a direct child."""
    in_policy, child_indent, found, seen_policy = False, None, False, False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            key = line.split(":", 1)[0].strip()
            if key == "policy" and seen_policy:
                return False  # duplicate policy: ambiguous
            in_policy = re.fullmatch(r"policy:\s*(#.*)?", line.strip()) is not None
            seen_policy = seen_policy or key == "policy"
            child_indent = None
            continue
        if not in_policy:
            continue
        if child_indent is None:
            child_indent = indent
        if indent == child_indent:
            m = re.fullmatch(r"allow_implicit_invocation:\s+(\S+)\s*(#.*)?", line.strip())
            if m:
                if found:
                    return False  # duplicate key: ambiguous
                found = m.group(1) == "false"
                if not found:
                    return False
    return found


def strip_code_blocks(text: str) -> str:
    """Drop fenced code blocks but keep inline code."""
    out: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        m = FENCE_RE.match(line.strip())
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
                continue
            out.append(line)
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and not line.strip()[len(m.group(1)):].strip():
            fence = None
    return "\n".join(out)


def strip_code(text: str) -> str:
    """Drop fenced code blocks and inline code so links inside them are ignored."""
    out: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        m = FENCE_RE.match(line.strip())
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
                continue
            out.append(re.sub(r"`[^`]*`", "", line))
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and not line.strip()[len(m.group(1)):].strip():
            fence = None
    return "\n".join(out)


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.skill_text = ""
        self.findings: list[dict[str, str]] = []

    def read(self, path: Path) -> str | None:
        """Read a UTF-8 file, recording a finding instead of raising."""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            self.add("error", f"cannot read {path.relative_to(self.root).as_posix()}: {exc.__class__.__name__}")
            return None

    def add(self, level: str, msg: str) -> None:
        self.findings.append({"skill": self.root.name, "level": level, "message": msg})

    def run(self) -> list[dict[str, str]]:
        text = self.read(self.root / "SKILL.md")
        if text is None:
            return self.findings
        self.skill_text = text
        fields, err = parse_frontmatter(text)
        if err:
            self.add("error", err)
        for e in type_errors(fields):
            self.add("error", e)
        name, desc = fields.get("name", ""), fields.get("description", "")
        self.check_name(name if isinstance(name, str) else "")
        self.check_description(desc.strip() if isinstance(desc, str) else "")
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
        self.check_coupling()
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

    def check_keys(self, fields: dict[str, object]) -> None:
        for k in fields:
            if k == "allowed-tools":
                self.add("warning", "'allowed-tools' is experimental and harness-specific")
            elif k not in SPEC_KEYS | EXTENSION_KEYS:
                self.add("warning", f"frontmatter key '{k}' is neither a spec field nor a known extension")
        user_only = fields.get("disable-model-invocation") is True
        if user_only and fields.get("user-invocable") is False:
            self.add("error", "both invocation paths are disabled; the skill is unreachable")
        sidecar = self.root / "agents" / "openai.yaml"
        sidecar_text = self.read(sidecar) if sidecar.is_file() else ""
        desc = fields.get("description")
        body = self.skill_text.split("\n---", 2)[-1] if self.skill_text.startswith("---") else self.skill_text
        visible = (desc if isinstance(desc, str) else "") + "\n" + strip_code(body)
        if user_only and not re.search(r"explicitly invoke", visible, re.I):
            self.add("error", "user-only skill must say 'Run only when the user explicitly invokes it' in its description or body")
        compat = fields.get("compatibility")
        codex_excluded = isinstance(compat, str) and re.search(r"\bonly\b", compat, re.I) and "codex" not in compat.lower()
        if user_only and not codex_excluded and not sidecar_disables_implicit(sidecar_text or ""):
            self.add("error", "user-only skill needs agents/openai.yaml setting policy.allow_implicit_invocation: false")
        if isinstance(compat, str) and len(compat) > 500:
            self.add("error", "compatibility exceeds 500 chars")

    def check_intent(self) -> None:
        intent = self.root / "INTENT.md"
        if not intent.is_file():
            return
        text = self.read(intent)
        if text is None:
            return
        for heading in ("## Goals", "## Requirements", "## Log"):
            if not re.search(rf"^{re.escape(heading)}\s*$", text, re.M):
                self.add("warning", f"INTENT.md has no '{heading}' section")

    def check_layout(self) -> None:
        refs = self.root / "references"
        if refs.is_dir():
            for p in refs.rglob("*"):
                if p.is_file() and p.parent != refs:
                    self.add("warning", f"{p.relative_to(self.root).as_posix()} is nested; keep references one level deep")

    def check_coupling(self) -> None:
        """Warn when agent-facing text names a sibling skill or instruction file."""
        names = coupling_names(self.root)
        if not names:
            return
        docs = [self.root / "SKILL.md"]
        refs = self.root / "references"
        if refs.is_dir():
            docs += sorted(refs.glob("*.md"))
        for doc in docs:
            text = self.read(doc) if doc.is_file() else None
            if text is None:
                continue
            prose = strip_code_blocks(text)
            for kind, name in names:
                n = re.escape(name)
                # Unambiguous references only: the name in inline code, an instruction
                # filename, or a hyphenated name next to its type. Plain words such as
                # "general" are ordinary prose.
                pattern = rf"`{n}(?:\.instructions\.md)?`|\b{n}\.instructions\.md\b"
                if "-" in name:
                    pattern += rf"|\b{n}\b(?:'s)?\s+{kind}s?\b|\b{kind}s?\s+\b{n}\b"
                if re.search(pattern, prose):
                    where = doc.relative_to(self.root).as_posix()
                    self.add("warning", f"{where} names the {kind} '{name}'; describe the capability instead so the skill stands alone")

    def check_links(self) -> None:
        docs = [self.root / "SKILL.md", self.root / "README.md"]
        refs = self.root / "references"
        if refs.is_dir():
            docs += sorted(refs.glob("*.md"))
        for doc in docs:
            if not doc.is_file():
                continue
            text = self.read(doc)
            if text is None:
                continue
            for target in LINK_RE.findall(strip_code(text)):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1]
                path = target.split("#", 1)[0]
                if "<" in path:
                    continue
                where = doc.relative_to(self.root).as_posix()
                resolved = (doc.parent / path).resolve()
                if not resolved.exists():
                    self.add("error", f"{where}: broken link '{target}'")
                elif resolved != self.root and self.root not in resolved.parents:
                    self.add("error", f"{where}: link '{target}' leaves the skill folder and breaks once installed")


def coupling_names(skill_root: Path) -> list[tuple[str, str]]:
    """Sibling skills and library instruction files a skill could name, as (kind, name)."""
    names: list[tuple[str, str]] = []
    parent = skill_root.parent
    try:
        names += [("skill", d.name) for d in parent.iterdir() if d != skill_root and (d / "SKILL.md").is_file()]
        instructions = parent.parent / "instructions"
        if instructions.is_dir():
            names += [("instruction", f.name.split(".")[0]) for f in instructions.glob("*.instructions.md")]
    except OSError:
        pass
    return names


def find_skills(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """Return (skill folders found, arguments that resolved to no skill)."""
    found: list[Path] = []
    missing: list[Path] = []
    for p in paths:
        if (p / "SKILL.md").is_file():
            found.append(p)
            continue
        try:
            subs = sorted(d for d in p.iterdir() if (d / "SKILL.md").is_file()) if p.is_dir() else []
        except OSError:
            subs = []
        if subs:
            found += subs
        else:
            missing.append(p)
    return found, missing


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check agent skill folders against the skill-development standards.",
        epilog="example: python3 check_skill.py skills/my-skill",
    )
    ap.add_argument("paths", nargs="+", type=Path, help="skill folder(s) or a folder of skills")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    args = ap.parse_args(argv)

    skills, missing = find_skills([p.resolve() for p in args.paths])
    findings = [{"skill": str(m), "level": "error", "message": "no SKILL.md here or in its subfolders"} for m in missing]
    if not skills:
        if args.json:
            print(json.dumps({"skills": 0, "errors": len(findings), "findings": findings}, indent=2))
        print("error: no folder with a SKILL.md found", file=sys.stderr)
        return 2
    findings += [f for s in skills for f in Checker(s).run()]
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
