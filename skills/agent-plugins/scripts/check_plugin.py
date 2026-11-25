#!/usr/bin/env python3
"""Check agent plugins and marketplace catalogs across plugin flavors.

Usage:
    python3 check_plugin.py <plugin-or-marketplace-root> [--json]

Reads, when present at the given root:
  - Agent Plugins 1.0: plugin.json, mcp.json, skills/
  - Claude Code: .claude-plugin/plugin.json, or its default layout without a manifest
  - Copilot legacy: plugin.json without $schema
  - Codex compatibility: .codex-plugin/plugin.json and extensions["com.openai"] paths
  - Catalogs: .claude-plugin/marketplace.json, .github/plugin/marketplace.json,
    .agents/plugins/marketplace.json
Each plugin a catalog lists by a local path is checked too.

Prints findings (JSON with --json). Exits 1 when any error is found, 2 on bad usage.
Stdlib only, Python 3.9+, any OS. It never writes files or fetches anything. Files that
resolve outside the checked root (symlinks, junctions) are reported and never read.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

SPEC_VERSIONS = ("1.0.0",)
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/{}/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/{}/mcp.schema.json"
CORE_FIELDS = {"$schema", "name", "version", "description", "author", "homepage", "repository",
               "license", "keywords", "extensions"}
COMPONENT_KEYS = {"skills", "commands", "agents", "hooks", "mcpServers", "lspServers", "outputStyles"}
CLAUDE_REPLACING_KEYS = {"skills", "commands", "agents", "hooks", "outputStyles", "themes"}
CLAUDE_LAYOUT = ("skills", "commands", "agents", "hooks/hooks.json", ".mcp.json", ".lsp.json", "output-styles")
CODEX_PATH_KEYS = ("apps", "onboardingSkill", "hooks")
CLAUDE_INLINE_KEYS = {"commands", "hooks", "mcpServers", "lspServers"}
NAME_10 = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
NAME_KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAMESPACE = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)+$")
HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
HEADER_VALUE = re.compile(r"^[^\x00-\x08\x0a-\x1f\x7f]*$")
CLAUDE_RESERVED_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
CLAUDE_RESERVED_NAMES = {"claude", "anthropic", "anthropics", "claude-code", "claude-mods"}
CLAUDE_RESERVED_MARKETPLACES = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills", "life-sciences", "knowledge-work-plugins",
    "first-party-plugins", "claude-community", "claude-plugins-community", "anthropic-plugin-directory",
    "claude-plugin-directory", "inline", "builtin", "skills-dir", "synced", "npm", "pip", "uv", "cargo",
    "github", "gh",
}
CATALOGS = {
    "claude": Path(".claude-plugin/marketplace.json"),
    "copilot": Path(".github/plugin/marketplace.json"),
    "copilot-root": Path("marketplace.json"),
    "codex": Path(".agents/plugins/marketplace.json"),
}
# Required locator fields for remote sources, per catalog flavor.
REMOTE_SOURCES = {
    "claude": {"github": ("repo",), "url": ("url",), "git-subdir": ("url", "path"), "npm": ("package",),
               "archive": ("url",), "command": ("command",)},
    "copilot": {"github": ("repo",), "url": ("url",)},
    "copilot-root": {"github": ("repo",), "url": ("url",)},
    "codex": {"url": ("url",), "git-subdir": ("url", "path"), "npm": ("package",)},
}
CODEX_INSTALL = {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}
CODEX_AUTH = {"ON_INSTALL", "ON_FIRST_USE"}
STDIO_FIELDS = {"type", "command", "args", "env", "cwd"}
HTTP_FIELDS = {"type", "url", "headers"}
CWD = re.compile(r"^(?:\./.*|\$\{PLUGIN_(?:ROOT|DATA)\}(?:/.*)?)$")


def is_str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def frontmatter_scalar(front: str, key: str) -> str | None:
    """Return a top-level YAML scalar from frontmatter, or None when absent, empty, or null.

    Handles plain, quoted, and block (| or >) scalars; enough for name and description.
    """
    lines = front.splitlines()
    for i, line in enumerate(lines):
        m = re.match(rf"{re.escape(key)}:(?:[ \t]+(.*))?$", line)
        if not m:
            continue
        rest = (m.group(1) or "").strip()
        if rest[:1] in ("|", ">") or rest == "" or rest.startswith("#"):
            block = []
            for nxt in lines[i + 1:]:
                if nxt.strip() and not nxt[:1].isspace():
                    break
                block.append(nxt.strip())
            text = " ".join(x for x in block if x)
            return text or None
        if rest[0] in "'\"":
            q = rest[0]
            end = rest.find(q, 1)
            while q == "'" and end != -1 and rest[end + 1:end + 2] == "'":
                end = rest.find(q, end + 2)
            value = rest[1:end] if end != -1 else rest[1:]
            return value.replace("''", "'") if q == "'" else value
        value = re.split(r"[ \t]#", rest, maxsplit=1)[0].strip()
        return None if value in ("~", "null", "Null", "NULL") else value
    return None


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.findings: list[dict[str, str]] = []
        self.plugins: dict[Path, dict[str, str]] = {}
        self.catalogs: dict[str, dict] = {}
        self.outside: set[Path] = set()

    # -- helpers -----------------------------------------------------------
    def add(self, level: str, path: Path, message: str) -> None:
        try:
            shown = Path(os.path.abspath(path)).relative_to(self.root).as_posix() or "."
        except ValueError:
            shown = str(path)
        self.findings.append({"level": level, "path": shown, "message": message})

    def error(self, path: Path, message: str) -> None:
        self.add("error", path, message)

    def warn(self, path: Path, message: str) -> None:
        self.add("warning", path, message)

    @staticmethod
    def inside(base: Path, target: Path) -> bool:
        try:
            target.resolve().relative_to(base.resolve())
            return True
        except (ValueError, OSError, RuntimeError):
            return False

    def contained(self, base: Path, path: Path) -> bool:
        """True when path resolves inside base. Reports it once otherwise."""
        if self.inside(base, path):
            return True
        key = Path(os.path.abspath(path))
        if key not in self.outside:
            self.outside.add(key)
            self.error(path, "resolves outside the root (symlink or junction); it is not read and "
                             "is missing after install")
        return False

    def load(self, path: Path, base: Path):
        if not self.contained(base, path):
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError) as exc:
            self.error(path, f"cannot read: {exc}")
            return None
        except json.JSONDecodeError as exc:
            self.error(path, f"invalid JSON: {exc}")
            return None
        if not isinstance(data, dict):
            self.error(path, "top level must be a JSON object")
            return None
        return data

    def check_rel_path(self, base: Path, value: str, where: Path, what: str) -> Path | None:
        if "\\" in value:
            self.error(where, f"{what} {value!r}: use forward slashes")
            return None
        if ".." in Path(value).parts:
            self.error(where, f"{what} {value!r}: must not contain '..'")
            return None
        if not value.startswith("./"):
            self.error(where, f"{what} {value!r}: must start with './'")
            return None
        target = base / value
        if not self.inside(base, target):
            self.error(where, f"{what} {value!r}: resolves outside the root")
            return None
        if not target.exists():
            self.error(where, f"{what} {value!r}: not found")
            return None
        return target

    def check_path_values(self, base: Path, value, where: Path, what: str) -> None:
        """Check a string or list of strings as ./ paths; leave inline objects alone."""
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, str):
                self.check_rel_path(base, item, where, what)
            elif not isinstance(item, dict):
                self.error(where, f"{what} must be a path, a list of paths, or an inline object")

    # -- plugins -----------------------------------------------------------
    def check_plugin(self, d: Path, entry_components: bool = False) -> dict[str, str]:
        d = d.resolve()
        if d in self.plugins:
            return self.plugins[d]
        info: dict[str, str] = {}
        self.plugins[d] = info
        self.scan_tree(d)
        names: dict[str, str] = {}
        versions: dict[str, str] = {}
        spec_version = None

        def remember(label: str, data: dict) -> None:
            if isinstance(data.get("name"), str):
                names[label] = data["name"]
            if isinstance(data.get("version"), str):
                versions[label] = data["version"]

        root_manifest = d / "plugin.json"
        root_data = self.load(root_manifest, d) if root_manifest.is_file() else None
        if root_data is not None:
            if "$schema" not in root_data:
                info["format"] = "copilot-legacy"
                self.warn(root_manifest, "no $schema: Copilot reads this as its legacy format and other "
                                         "clients reject it; add the Agent Plugins 1.0 $schema")
                self.check_manifest_legacy(d, root_manifest, root_data)
            else:
                schema = root_data["$schema"]
                spec_version = next((v for v in SPEC_VERSIONS if schema == PLUGIN_SCHEMA.format(v)), None)
                other = re.fullmatch(r"https://agent-plugins\.org/schemas/([0-9][0-9A-Za-z.+-]*)/plugin\.schema\.json",
                                     str(schema))
                if spec_version is None and other:
                    info["format"] = f"agent-plugins-{other.group(1)}"
                    self.warn(root_manifest, f"Agent Plugins {other.group(1)} is not implemented by this checker "
                                             f"(it validates {', '.join(SPEC_VERSIONS)}); only paths and skills are "
                                             "checked. Validate with each target client")
                elif spec_version is None:
                    self.error(root_manifest, f"unknown $schema {schema!r}; Agent Plugins 1.0 uses "
                                              f"{PLUGIN_SCHEMA.format(SPEC_VERSIONS[-1])!r}")
                else:
                    info["format"] = f"agent-plugins-{spec_version}"
                    self.check_manifest_10(d, root_manifest, root_data)
            remember("plugin.json", root_data)

        mcp = d / "mcp.json"
        if mcp.is_file():
            if spec_version:
                data = self.load(mcp, d)
                if data is not None:
                    self.check_mcp_10(d, mcp, data, spec_version)
            else:
                self.warn(mcp, "mcp.json is the Agent Plugins MCP file, but plugin.json is not an "
                               "Agent Plugins manifest")

        claude_dir = d / ".claude-plugin"
        claude_manifest = claude_dir / "plugin.json"
        if claude_manifest.is_file():
            data = self.load(claude_manifest, d)
            if data is not None:
                info["claude"] = "yes"
                self.check_manifest_claude(d, claude_manifest, data)
                remember(".claude-plugin/plugin.json", data)
        if claude_dir.is_dir() and self.inside(d, claude_dir):
            extra = sorted(p.name for p in claude_dir.iterdir() if p.name not in {"plugin.json", "marketplace.json"})
            if extra:
                self.warn(claude_dir, f"only manifests belong in .claude-plugin/; move {', '.join(extra)} "
                                      "to the plugin root")

        open_manifest = d / ".plugin" / "plugin.json"
        if open_manifest.is_file():
            data = self.load(open_manifest, d)
            if data is not None:
                self.warn(open_manifest, "legacy OpenPlugin manifest; migrate to a root Agent Plugins plugin.json")
                self.check_manifest_legacy(d, open_manifest, data)
                remember(".plugin/plugin.json", data)

        codex_manifest = d / ".codex-plugin" / "plugin.json"
        if codex_manifest.is_file():
            data = self.load(codex_manifest, d)
            if data is not None:
                ext = (root_data or {}).get("extensions")
                if isinstance(ext, dict) and "com.openai" in ext:
                    self.warn(codex_manifest, "ignored: plugin.json already has extensions['com.openai']")
                else:
                    self.check_codex_paths(d, codex_manifest, data, "")
                    inner = data.get("extensions")
                    if isinstance(inner, dict) and isinstance(inner.get("com.openai"), dict):
                        self.check_codex_paths(d, codex_manifest, inner["com.openai"], "extensions.com.openai.")
                remember(".codex-plugin/plugin.json", data)

        if len(set(names.values())) > 1:
            self.error(d, "plugin name differs between manifests: "
                          + ", ".join(f"{k}={v!r}" for k, v in names.items()))
        if len(set(versions.values())) > 1:
            self.warn(d, "version differs between manifests: "
                         + ", ".join(f"{k}={v!r}" for k, v in versions.items()))
        if names:
            info["name"] = next(iter(names.values()))
        has_layout = any((d / p).exists() for p in CLAUDE_LAYOUT)
        if not names and not has_layout and not entry_components:
            self.error(d, "no plugin manifest and no plugin components")
        elif root_data is None and not entry_components:
            self.warn(d, "no root plugin.json; Agent Plugins 1.0 clients will not load this plugin")

        self.check_skills(d, portable=spec_version is not None)
        return info

    def scan_tree(self, d: Path) -> None:
        """Report entries that resolve outside d, without descending into them."""
        stack = [d]
        while stack:
            current = stack.pop()
            try:
                entries = list(os.scandir(current))
            except OSError as exc:
                self.error(current, f"cannot list: {exc}")
                continue
            for entry in entries:
                if entry.name == ".git":
                    continue
                p = Path(entry.path)
                if not self.contained(d, p):
                    continue
                try:
                    broken = p.is_symlink() and not p.exists()
                except (OSError, RuntimeError):
                    broken = True
                if broken:
                    self.error(p, "symlink is broken or loops; it resolves outside the root or nowhere")
                    continue
                try:
                    if entry.is_dir(follow_symlinks=False) and not p.is_symlink():
                        stack.append(p)
                except OSError:
                    continue

    def check_manifest_10(self, d: Path, path: Path, data: dict) -> None:
        for key in sorted(set(data) - CORE_FIELDS):
            hint = ("component paths are not part of Agent Plugins 1.0; use the fixed locations, and put "
                    "Claude-only keys in .claude-plugin/plugin.json") if key in COMPONENT_KEYS else \
                "not an Agent Plugins 1.0 field; clients ignore it. Put client data under 'extensions'"
            self.warn(path, f"'{key}': {hint}")
        name = data.get("name")
        if not isinstance(name, str):
            self.error(path, "'name' is required and must be a string")
        elif not NAME_10.match(name) or "--" in name or ".." in name:
            self.error(path, f"name {name!r}: 1-64 of a-z 0-9 - . , alphanumeric at both ends, no '--' or '..'")
        for key in ("version", "description", "homepage", "repository", "license"):
            if key in data and not isinstance(data[key], str):
                self.error(path, f"'{key}' must be a string")
        if "keywords" in data and not is_str_list(data["keywords"]):
            self.error(path, "'keywords' must be an array of strings")
        if "author" in data:
            author = data["author"]
            if not isinstance(author, dict):
                self.error(path, "'author' must be an object")
            else:
                for key, value in author.items():
                    if key not in {"name", "email", "url"}:
                        self.error(path, f"author.{key}: only name, email, and url are allowed")
                    elif not isinstance(value, str):
                        self.error(path, f"author.{key} must be a string")
        if "extensions" in data:
            ext = data["extensions"]
            if not isinstance(ext, dict):
                self.warn(path, "'extensions' must be an object; clients ignore it")
                return
            for key, value in ext.items():
                if not NAMESPACE.match(key):
                    self.warn(path, f"extensions.{key}: use a reverse-domain namespace such as com.example.client")
                if not isinstance(value, dict):
                    self.error(path, f"extensions.{key} must be an object")
            openai = ext.get("com.openai")
            if isinstance(openai, dict):
                self.check_codex_paths(d, path, openai, "extensions.com.openai.")

    def check_codex_paths(self, d: Path, path: Path, data: dict, prefix: str) -> None:
        for key in CODEX_PATH_KEYS:
            if key in data:
                self.check_path_values(d, data[key], path, f"{prefix}{key}")

    def check_manifest_legacy(self, d: Path, path: Path, data: dict) -> None:
        if not isinstance(data.get("name"), str):
            self.error(path, "'name' is required")
        for key in sorted(COMPONENT_KEYS & set(data)):
            self.check_path_values(d, data[key], path, key)

    def check_mcp_10(self, d: Path, path: Path, data: dict, version: str) -> None:
        expected = MCP_SCHEMA.format(version)
        if data.get("$schema") != expected:
            self.error(path, f"$schema must be {expected!r} to match plugin.json; clients disable MCP otherwise")
        for key in sorted(set(data) - {"$schema", "mcpServers"}):
            self.error(path, f"'{key}': only $schema and mcpServers are allowed")
        servers = data.get("mcpServers")
        if not isinstance(servers, dict):
            self.error(path, "'mcpServers' is required and must be an object")
            return
        for name, server in servers.items():
            where = f"mcpServers.{name}"
            if not isinstance(server, dict):
                self.error(path, f"{where} must be an object")
                continue
            if "extensions" in server:
                self.warn(path, f"{where}.extensions is a client extension (Codex reads auth there), not a "
                                "portable server field; strict Agent Plugins clients may skip this server")
            kind = server.get("type")
            if kind == "stdio":
                self.check_fields(path, where, server, STDIO_FIELDS, "stdio")
                self.check_stdio(d, path, where, server)
            elif kind in ("streamable-http", "sse"):
                if kind == "sse":
                    self.warn(path, f"{where}: sse is deprecated and not supported by every client; "
                                    "use streamable-http")
                self.check_fields(path, where, server, HTTP_FIELDS, kind)
                self.check_http(path, where, server)
            else:
                self.error(path, f"{where}.type must be stdio, streamable-http, or sse")

    def check_fields(self, path: Path, where: str, server: dict, allowed: set, kind: str) -> None:
        for key in sorted(set(server) - allowed - {"extensions"}):
            self.error(path, f"{where}.{key}: not a {kind} field; clients skip this server")

    def check_stdio(self, d: Path, path: Path, where: str, server: dict) -> None:
        command = server.get("command")
        if not isinstance(command, str) or not command:
            self.error(path, f"{where}.command is required")
        elif re.search(r"\s", command) or "${" in command:
            self.error(path, f"{where}.command must be one executable token with no variables; "
                             "put arguments in args")
        elif "/" in command or "\\" in command:
            if not command.startswith("./"):
                self.error(path, f"{where}.command must be a bare name or a './' path inside the plugin")
            else:
                target = self.check_rel_path(d, command, path, f"{where}.command")
                if target is not None and not target.is_file():
                    self.error(path, f"{where}.command {command!r} is not a file")
        if "args" in server and not is_str_list(server["args"]):
            self.error(path, f"{where}.args must be an array of strings")
        if "env" in server:
            env = server["env"]
            if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()):
                self.error(path, f"{where}.env must map names to strings")
            else:
                for key in ("PLUGIN_ROOT", "PLUGIN_DATA"):
                    if key in env:
                        self.error(path, f"{where}.env must not set {key}; the client provides it")
        if "cwd" in server:
            cwd = server["cwd"]
            if not isinstance(cwd, str) or "\\" in cwd or not CWD.fullmatch(cwd) or ".." in cwd.split("/"):
                self.error(path, f"{where}.cwd must be './...', '${{PLUGIN_ROOT}}[/...]', or '${{PLUGIN_DATA}}[/...]'")

    def check_http(self, path: Path, where: str, server: dict) -> None:
        url = server.get("url")
        if not isinstance(url, str):
            self.error(path, f"{where}.url is required")
        else:
            try:
                parts = urlsplit(url)
                host = parts.hostname
                _ = parts.port  # raises ValueError for a bad port
            except ValueError as exc:
                self.error(path, f"{where}.url is malformed: {exc}")
            else:
                if parts.scheme not in ("http", "https") or not host:
                    self.error(path, f"{where}.url must be an absolute http or https URL")
                elif parts.username is not None or parts.password is not None or parts.fragment:
                    self.error(path, f"{where}.url must not contain credentials or a fragment")
                elif parts.scheme == "http" and not is_loopback(host):
                    self.error(path, f"{where}.url must use https unless it is loopback")
        if "headers" in server:
            headers = server["headers"]
            if not isinstance(headers, dict):
                self.error(path, f"{where}.headers must be an object")
                return
            seen: set[str] = set()
            for key, value in headers.items():
                if not HEADER_NAME.fullmatch(key):
                    self.error(path, f"{where}.headers: {key!r} is not a valid header name")
                if key.lower() in seen:
                    self.error(path, f"{where}.headers: {key!r} duplicates another header (names are case-insensitive)")
                seen.add(key.lower())
                if not isinstance(value, str) or not HEADER_VALUE.fullmatch(value):
                    self.error(path, f"{where}.headers.{key} must be a string without control characters")

    def check_manifest_claude(self, d: Path, path: Path, data: dict) -> None:
        name = data.get("name")
        if not isinstance(name, str):
            self.error(path, "'name' is required")
        else:
            if not NAME_KEBAB.match(name):
                self.error(path, f"name {name!r}: Claude Code requires kebab-case")
            if name in CLAUDE_RESERVED_NAMES or name.startswith(CLAUDE_RESERVED_PREFIXES):
                self.error(path, f"name {name!r} is reserved by Claude Code")
        if str(data.get("$schema", "")).startswith("https://agent-plugins.org/"):
            self.warn(path, "the Agent Plugins $schema belongs in the root plugin.json, not here")
        self.check_claude_components(d, path, data, "")

    def check_claude_components(self, d: Path, path: Path, data: dict, prefix: str) -> None:
        entry = bool(prefix)
        for key in sorted(COMPONENT_KEYS & set(data)):
            raw = data[key]
            if entry and key == "hooks" and not isinstance(raw, dict):
                self.error(path, f"{prefix}hooks: a catalog entry accepts only inline hooks; put hook files "
                                 "in the plugin and reference them from its manifest")
                continue
            if isinstance(raw, dict):
                if key not in CLAUDE_INLINE_KEYS:
                    self.error(path, f"{prefix}{key} must be a path or a list of paths")
                continue
            values = raw if isinstance(raw, list) else [raw]
            for value in values:
                if isinstance(value, dict) and key in CLAUDE_INLINE_KEYS - {"commands"}:
                    continue
                if not isinstance(value, str):
                    self.error(path, f"{prefix}{key}: {value!r} is not a valid value")
                    continue
                if key == "skills" and value in (".", "./"):
                    continue
                if key == "mcpServers" and value.startswith("https://"):
                    continue
                target = self.check_rel_path(d, value, path, f"{prefix}{key}")
                if key == "mcpServers" and target is not None and target.name == "mcp.json":
                    self.warn(path, "mcpServers points at the Agent Plugins mcp.json; its schema and "
                                    "variables differ. Use .mcp.json or inline servers")

    def check_skills(self, d: Path, portable: bool) -> None:
        skills = d / "skills"
        if not skills.is_dir() or not self.inside(d, skills):
            return
        for child in sorted(skills.iterdir()):
            if not self.inside(d, child) or not child.is_dir():
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.is_file():
                self.warn(child, "no SKILL.md directly inside; clients skip it (no recursive search)")
                continue
            if not self.contained(d, skill_md):
                continue
            try:
                text = skill_md.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError) as exc:
                self.error(skill_md, f"cannot read: {exc}")
                continue
            match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
            front = match.group(1) if match else ""
            name = frontmatter_scalar(front, "name")
            desc = frontmatter_scalar(front, "description")
            report = self.error if portable else self.warn
            if not name:
                if portable:
                    self.error(skill_md, "frontmatter 'name' is required by Agent Skills; portable clients skip it")
            elif name != child.name:
                report(skill_md, f"name {name!r} must equal the folder name {child.name!r}")
            if not desc:
                report(skill_md, "frontmatter 'description' is required by Agent Skills")

    # -- catalogs ----------------------------------------------------------
    def check_catalogs(self) -> None:
        for kind, rel in CATALOGS.items():
            path = self.root / rel
            if path.is_file():
                data = self.load(path, self.root)
                if data is not None:
                    self.catalogs[kind] = self.check_catalog(kind, path, data)
        if "copilot" in self.catalogs and "copilot-root" in self.catalogs:
            self.warn(self.root / "marketplace.json", "Copilot loads one catalog; keep either marketplace.json or "
                                                     ".github/plugin/marketplace.json, not both")
        if len(self.catalogs) < 2:
            return
        union = sorted(set().union(*(set(v) for v in self.catalogs.values())))
        for kind, entries in self.catalogs.items():
            missing = [n for n in union if n not in entries]
            if missing:
                self.warn(self.root / CATALOGS[kind], f"missing plugins listed in other catalogs: {', '.join(missing)}")
        for name in union:
            listing = {k: v[name] for k, v in self.catalogs.items() if name in v}
            if len(listing) < 2:
                continue
            for field in ("description", "version"):
                values = {k: e.get(field) for k, e in listing.items()}
                if len({json.dumps(x) for x in values.values()}) > 1:
                    self.warn(self.root, f"{name}: {field} differs between catalogs: {values}")

    def check_catalog(self, kind: str, path: Path, data: dict) -> dict[str, dict]:
        entries: dict[str, dict] = {}
        name = data.get("name")
        if not isinstance(name, str) or not name:
            self.error(path, "'name' is required")
        elif kind == "claude":
            if name.lower() in CLAUDE_RESERVED_MARKETPLACES or name.lower().startswith("claudeai-"):
                self.error(path, f"marketplace name {name!r} is reserved by Claude Code")
            if re.search(r"[\s/\\]", name) or name in {".", ".."} or ".." in name:
                self.error(path, f"marketplace name {name!r}: no spaces, slashes, or '..'")
        if kind != "codex":
            owner = data.get("owner")
            if not (isinstance(owner, dict) and isinstance(owner.get("name"), str)):
                self.error(path, "'owner.name' is required")
        plugins = data.get("plugins")
        if not isinstance(plugins, list):
            self.error(path, "'plugins' is required and must be an array")
            return entries
        metadata = data.get("metadata")
        plugin_root = metadata.get("pluginRoot") if isinstance(metadata, dict) else None
        for i, entry in enumerate(plugins):
            where = f"plugins[{i}]"
            if not isinstance(entry, dict):
                self.error(path, f"{where} must be an object")
                continue
            ename = entry.get("name")
            if not isinstance(ename, str) or not ename:
                self.error(path, f"{where}.name is required")
                continue
            where = f"plugins[{ename}]"
            if ename in entries:
                self.error(path, f"duplicate plugin name {ename!r}")
            entries[ename] = entry
            if kind == "codex":
                self.check_codex_entry(path, where, entry)
            local = self.local_source(kind, path, where, entry.get("source"), plugin_root)
            if local is None:
                continue
            supplies = kind == "claude" and bool((COMPONENT_KEYS | {"themes"}) & set(entry))
            info = self.check_plugin(local, entry_components=supplies)
            if info.get("name") and info["name"] != ename:
                self.error(path, f"{where}: entry name differs from the plugin manifest name {info['name']!r}")
            if kind == "claude":
                self.check_claude_entry(path, where, entry, local)
        return entries

    def local_source(self, kind: str, path: Path, where: str, source, plugin_root) -> Path | None:
        if source is None:
            self.error(path, f"{where}.source is required")
            return None
        if isinstance(source, dict):
            stype = source.get("source")
            if kind == "codex" and stype == "local":
                source = source.get("path")
                if not isinstance(source, str):
                    self.error(path, f"{where}.source.path is required for local sources")
                    return None
            else:
                known = REMOTE_SOURCES[kind]
                if not isinstance(stype, str):
                    self.error(path, f"{where}.source object needs a 'source' type")
                elif stype not in known:
                    self.error(path, f"{where}.source type {stype!r} is not supported here; use one of "
                                     f"{', '.join(sorted(known))}")
                else:
                    for field in known[stype]:
                        if not isinstance(source.get(field), str) or not source[field]:
                            self.error(path, f"{where}.source.{field} is required for {stype} sources")
                    if stype == "archive" and not str(source.get("url", "")).startswith("https://"):
                        self.error(path, f"{where}.source.url must be https for archive sources")
                return None
        if not isinstance(source, str):
            self.error(path, f"{where}.source must be a string or an object")
            return None
        if kind.startswith("copilot") and source not in (".", "") and not source.startswith(("./", "/")) \
                and "://" not in source:
            source = "./" + source
        if kind == "claude" and source in (".", "./"):
            return self.root
        if kind == "claude" and isinstance(plugin_root, str) and re.fullmatch(r"[^/\\.][^/\\]*", source):
            base = self.check_rel_path(self.root, plugin_root, path, "metadata.pluginRoot")
            return self.check_rel_path(base, "./" + source, path, f"{where}.source") if base else None
        return self.check_rel_path(self.root, source, path, f"{where}.source")

    def check_claude_entry(self, path: Path, where: str, entry: dict, local: Path) -> None:
        manifest = local / ".claude-plugin" / "plugin.json"
        if entry.get("strict") is False and manifest.is_file() and CLAUDE_REPLACING_KEYS & set(entry):
            self.error(path, f"{where}: strict false with component fields conflicts with "
                             f"{manifest.relative_to(self.root).as_posix()}; Claude Code refuses to load it")
        if "version" in entry and manifest.is_file() and self.inside(local, manifest):
            try:
                has_version = "version" in json.loads(manifest.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError, TypeError):
                has_version = False
            if has_version:
                self.warn(path, f"{where}: version is set in both the entry and the plugin manifest; "
                                "the manifest wins. Set it in one place")
        self.check_claude_components(local, path, entry, f"{where}.")

    def check_codex_entry(self, path: Path, where: str, entry: dict) -> None:
        policy = entry.get("policy")
        if not isinstance(policy, dict):
            self.warn(path, f"{where}.policy is expected by Codex (installation, authentication)")
        else:
            for key, allowed in (("installation", CODEX_INSTALL), ("authentication", CODEX_AUTH)):
                value = policy.get(key)
                if not isinstance(value, str) or value not in allowed:
                    self.warn(path, f"{where}.policy.{key} should be one of {', '.join(sorted(allowed))}")
        if not isinstance(entry.get("category"), str):
            self.warn(path, f"{where}.category is expected by Codex")

    # -- entry point -------------------------------------------------------
    def run(self) -> list[dict[str, str]]:
        is_plugin = any((self.root / p).is_file() for p in
                        ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"))
        has_catalog = any((self.root / p).is_file() for p in CATALOGS.values())
        has_layout = any((self.root / p).exists() for p in CLAUDE_LAYOUT)
        if is_plugin or (not has_catalog and has_layout):
            self.check_plugin(self.root)
        self.check_catalogs()
        if not self.plugins and not self.catalogs:
            self.error(self.root, "no plugin manifest, plugin components, or marketplace catalog found")
        return self.findings


def _rel(root: Path, p: Path) -> str:
    try:
        return p.relative_to(root).as_posix() or "."
    except ValueError:
        return str(p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check agent plugins and marketplace catalogs.")
    parser.add_argument("path", help="plugin folder or marketplace root")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)
    root = Path(args.path)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    checker = Checker(root)
    findings = checker.run()
    errors = sum(f["level"] == "error" for f in findings)
    if args.json:
        print(json.dumps({
            "plugins": [{"path": _rel(checker.root, p), **i} for p, i in checker.plugins.items()],
            "catalogs": sorted(checker.catalogs),
            "findings": findings,
        }, indent=2))
    else:
        for f in findings:
            print(f"{f['level'].upper()}: {f['path']}: {f['message']}")
        print(f"{len(checker.plugins)} plugin(s), {len(checker.catalogs)} catalog(s): "
              f"{errors} error(s), {len(findings) - errors} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
