#!/usr/bin/env python3
"""Check agent plugins and marketplace catalogs across plugin flavors.

Usage:
    python3 check_plugin.py <plugin-or-marketplace-root> [--json]

Reads, when present at the given root:
  - Agent Plugins 1.0: plugin.json, mcp.json, skills/
  - Claude Code: .claude-plugin/plugin.json
  - Codex compatibility: .codex-plugin/plugin.json
  - Catalogs: .claude-plugin/marketplace.json, .github/plugin/marketplace.json,
    .agents/plugins/marketplace.json
Each plugin a catalog lists by a local path is checked too.

Prints findings (JSON with --json). Exits 1 when any error is found, 2 on bad usage.
Stdlib only, Python 3.9+, any OS. It never writes files or fetches anything.
"""

from __future__ import annotations

import argparse
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
NAME_10 = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
NAME_KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAMESPACE = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)+$")
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
    "codex": Path(".agents/plugins/marketplace.json"),
}
CODEX_INSTALL = {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}
CODEX_AUTH = {"ON_INSTALL", "ON_FIRST_USE"}
LOOPBACK = {"localhost", "127.0.0.1", "::1"}
CWD = re.compile(r"^(?:\./.*|\$\{PLUGIN_(?:ROOT|DATA)\}(?:/.*)?)$")


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.findings: list[dict[str, str]] = []
        self.plugins: dict[Path, dict[str, str]] = {}
        self.catalogs: dict[str, dict] = {}

    # -- helpers -----------------------------------------------------------
    def add(self, level: str, path: Path, message: str) -> None:
        try:
            shown = path.resolve().relative_to(self.root).as_posix() or "."
        except ValueError:
            shown = str(path)
        self.findings.append({"level": level, "path": shown, "message": message})

    def error(self, path: Path, message: str) -> None:
        self.add("error", path, message)

    def warn(self, path: Path, message: str) -> None:
        self.add("warning", path, message)

    def load(self, path: Path):
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

    @staticmethod
    def inside(base: Path, target: Path) -> bool:
        try:
            target.resolve().relative_to(base.resolve())
            return True
        except ValueError:
            return False

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

    # -- plugins -----------------------------------------------------------
    def check_plugin(self, d: Path) -> dict[str, str]:
        d = d.resolve()
        if d in self.plugins:
            return self.plugins[d]
        info: dict[str, str] = {}
        self.plugins[d] = info
        names: dict[str, str] = {}
        versions: dict[str, str] = {}
        spec_version = None

        root_manifest = d / "plugin.json"
        root_data = self.load(root_manifest) if root_manifest.is_file() else None
        if root_data is not None:
            schema = root_data.get("$schema")
            if schema is None:
                info["format"] = "copilot-legacy"
                self.warn(root_manifest, "no $schema: Copilot reads this as its legacy format and other "
                                         "clients reject it; add the Agent Plugins 1.0 $schema")
                if not isinstance(root_data.get("name"), str):
                    self.error(root_manifest, "'name' is required")
            else:
                spec_version = next((v for v in SPEC_VERSIONS if schema == PLUGIN_SCHEMA.format(v)), None)
                if spec_version is None:
                    self.error(root_manifest, f"unknown $schema {schema!r}; Agent Plugins 1.0 uses "
                                              f"{PLUGIN_SCHEMA.format(SPEC_VERSIONS[-1])!r}")
                else:
                    info["format"] = f"agent-plugins-{spec_version}"
                    self.check_manifest_10(root_manifest, root_data)
            if isinstance(root_data.get("name"), str):
                names["plugin.json"] = root_data["name"]
            if isinstance(root_data.get("version"), str):
                versions["plugin.json"] = root_data["version"]

        mcp = d / "mcp.json"
        if mcp.is_file():
            if spec_version:
                data = self.load(mcp)
                if data is not None:
                    self.check_mcp_10(mcp, data, spec_version)
            else:
                self.warn(mcp, "mcp.json is the Agent Plugins MCP file, but plugin.json is not an "
                               "Agent Plugins manifest")

        claude_dir = d / ".claude-plugin"
        claude_manifest = claude_dir / "plugin.json"
        if claude_manifest.is_file():
            data = self.load(claude_manifest)
            if data is not None:
                info["claude"] = "yes"
                self.check_manifest_claude(d, claude_manifest, data)
                if isinstance(data.get("name"), str):
                    names[".claude-plugin/plugin.json"] = data["name"]
                if isinstance(data.get("version"), str):
                    versions[".claude-plugin/plugin.json"] = data["version"]
        if claude_dir.is_dir():
            extra = sorted(p.name for p in claude_dir.iterdir() if p.name not in {"plugin.json", "marketplace.json"})
            if extra:
                self.warn(claude_dir, f"only manifests belong in .claude-plugin/; move {', '.join(extra)} "
                                      "to the plugin root")

        codex_manifest = d / ".codex-plugin" / "plugin.json"
        if codex_manifest.is_file():
            data = self.load(codex_manifest)
            if data is not None:
                ext = (root_data or {}).get("extensions")
                if isinstance(ext, dict) and "com.openai" in ext:
                    self.warn(codex_manifest, "ignored: plugin.json already has extensions['com.openai']")
                if isinstance(data.get("name"), str):
                    names[".codex-plugin/plugin.json"] = data["name"]
                if isinstance(data.get("version"), str):
                    versions[".codex-plugin/plugin.json"] = data["version"]

        if len(set(names.values())) > 1:
            self.error(d, "plugin name differs between manifests: "
                          + ", ".join(f"{k}={v!r}" for k, v in names.items()))
        if len(set(versions.values())) > 1:
            self.warn(d, "version differs between manifests: "
                         + ", ".join(f"{k}={v!r}" for k, v in versions.items()))
        if names:
            info["name"] = next(iter(names.values()))
        if not names and not (d / "skills").is_dir():
            self.error(d, "no plugin manifest and no skills/ folder")
        elif root_data is None and not claude_manifest.is_file():
            self.warn(d, "no plugin manifest; Agent Plugins 1.0 clients need a root plugin.json")

        self.check_skills(d)
        self.check_links(d)
        return info

    def check_manifest_10(self, path: Path, data: dict) -> None:
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
        kw = data.get("keywords")
        if kw is not None and not (isinstance(kw, list) and all(isinstance(k, str) for k in kw)):
            self.error(path, "'keywords' must be an array of strings")
        author = data.get("author")
        if author is not None:
            if not isinstance(author, dict):
                self.error(path, "'author' must be an object")
            else:
                for key, value in author.items():
                    if key not in {"name", "email", "url"}:
                        self.error(path, f"author.{key}: only name, email, and url are allowed")
                    elif not isinstance(value, str):
                        self.error(path, f"author.{key} must be a string")
        ext = data.get("extensions")
        if ext is not None:
            if not isinstance(ext, dict):
                self.warn(path, "'extensions' must be an object; clients ignore it")
            else:
                for key, value in ext.items():
                    if not NAMESPACE.match(key):
                        self.warn(path, f"extensions.{key}: use a reverse-domain namespace such as com.example.client")
                    if not isinstance(value, dict):
                        self.error(path, f"extensions.{key} must be an object")

    def check_mcp_10(self, path: Path, data: dict, version: str) -> None:
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
            kind = server.get("type")
            if kind == "stdio":
                self.check_stdio(path, where, server)
            elif kind in ("streamable-http", "sse"):
                if kind == "sse":
                    self.warn(path, f"{where}: sse is deprecated and not supported by every client; "
                                    "use streamable-http")
                self.check_http(path, where, server)
            else:
                self.error(path, f"{where}.type must be stdio, streamable-http, or sse")

    def check_stdio(self, path: Path, where: str, server: dict) -> None:
        for key in sorted(set(server) - {"type", "command", "args", "env", "cwd"}):
            self.warn(path, f"{where}.{key}: not a stdio field")
        command = server.get("command")
        if not isinstance(command, str) or not command:
            self.error(path, f"{where}.command is required")
        elif re.search(r"\s", command) or "${" in command:
            self.error(path, f"{where}.command must be one executable token with no variables; "
                             "put arguments in args")
        elif ("/" in command or "\\" in command) and not command.startswith("./"):
            self.error(path, f"{where}.command must be a bare name or a './' path inside the plugin")
        args = server.get("args")
        if args is not None and not (isinstance(args, list) and all(isinstance(a, str) for a in args)):
            self.error(path, f"{where}.args must be an array of strings")
        env = server.get("env")
        if env is not None:
            if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()):
                self.error(path, f"{where}.env must map names to strings")
            else:
                for key in ("PLUGIN_ROOT", "PLUGIN_DATA"):
                    if key in env:
                        self.error(path, f"{where}.env must not set {key}; the client provides it")
        cwd = server.get("cwd")
        if cwd is not None and (not isinstance(cwd, str) or not CWD.match(cwd) or ".." in cwd.split("/")):
            self.error(path, f"{where}.cwd must be './...', '${{PLUGIN_ROOT}}[/...]', or '${{PLUGIN_DATA}}[/...]'")

    def check_http(self, path: Path, where: str, server: dict) -> None:
        for key in sorted(set(server) - {"type", "url", "headers"}):
            self.warn(path, f"{where}.{key}: not an HTTP server field")
        url = server.get("url")
        if not isinstance(url, str):
            self.error(path, f"{where}.url is required")
        else:
            parts = urlsplit(url)
            if parts.scheme not in ("http", "https") or not parts.hostname:
                self.error(path, f"{where}.url must be an absolute http or https URL")
            elif parts.username or parts.password or parts.fragment:
                self.error(path, f"{where}.url must not contain credentials or a fragment")
            elif parts.scheme == "http" and parts.hostname not in LOOPBACK:
                self.error(path, f"{where}.url must use https unless it is loopback")
        headers = server.get("headers")
        if headers is not None and not (isinstance(headers, dict) and all(isinstance(v, str) for v in headers.values())):
            self.error(path, f"{where}.headers must map names to strings")

    def check_manifest_claude(self, d: Path, path: Path, data: dict) -> None:
        name = data.get("name")
        if not isinstance(name, str):
            self.error(path, "'name' is required")
        else:
            if not NAME_KEBAB.match(name):
                self.error(path, f"name {name!r}: Claude Code requires kebab-case")
            if name in CLAUDE_RESERVED_NAMES or name.startswith(CLAUDE_RESERVED_PREFIXES):
                self.error(path, f"name {name!r} is reserved by Claude Code")
        if "$schema" in data and str(data["$schema"]).startswith("https://agent-plugins.org/"):
            self.warn(path, "the Agent Plugins $schema belongs in the root plugin.json, not here")
        for key in sorted(COMPONENT_KEYS & set(data)):
            values = data[key] if isinstance(data[key], list) else [data[key]]
            for value in values:
                if isinstance(value, str):
                    target = self.check_rel_path(d, value, path, key)
                    if key == "mcpServers" and target is not None and target.name == "mcp.json":
                        self.warn(path, "mcpServers points at the Agent Plugins mcp.json; its schema and "
                                        "variables differ. Use .mcp.json or inline servers")

    def check_skills(self, d: Path) -> None:
        skills = d / "skills"
        if not skills.is_dir():
            return
        for child in sorted(skills.iterdir()):
            if not child.is_dir():
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.is_file():
                self.warn(child, "no SKILL.md directly inside; clients skip it (no recursive search)")
                continue
            try:
                text = skill_md.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError) as exc:
                self.error(skill_md, f"cannot read: {exc}")
                continue
            match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
            found = re.search(r"^name:[ \t]*['\"]?([^'\"\s#]+)", match.group(1), re.M) if match else None
            if not found:
                self.error(skill_md, "frontmatter with a 'name' is required")
            elif found.group(1) != child.name:
                self.error(skill_md, f"name {found.group(1)!r} must equal the folder name {child.name!r}")

    def check_links(self, d: Path) -> None:
        for base, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if x != ".git"]
            for entry in list(dirs) + files:
                p = Path(base) / entry
                if p.is_symlink() and not self.inside(d, p):
                    self.error(p, "symlink points outside the plugin root; it is missing after install")

    # -- catalogs ----------------------------------------------------------
    def check_catalogs(self) -> None:
        for kind, rel in CATALOGS.items():
            path = self.root / rel
            if path.is_file():
                data = self.load(path)
                if data is not None:
                    self.catalogs[kind] = self.check_catalog(kind, path, data)
        if len(self.catalogs) > 1:
            sets = {k: set(v) for k, v in self.catalogs.items()}
            union = set().union(*sets.values())
            for kind, names in sets.items():
                missing = sorted(union - names)
                if missing:
                    self.warn(self.root / CATALOGS[kind], f"missing plugins listed in other catalogs: {', '.join(missing)}")
            for name in sorted(set.intersection(*sets.values())):
                for field in ("description", "version"):
                    values = {k: v[name].get(field) for k, v in self.catalogs.items()}
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
        if kind == "claude":
            owner = data.get("owner")
            if not (isinstance(owner, dict) and isinstance(owner.get("name"), str)):
                self.error(path, "'owner.name' is required")
        plugins = data.get("plugins")
        if not isinstance(plugins, list):
            self.error(path, "'plugins' is required and must be an array")
            return entries
        plugin_root = (data.get("metadata") or {}).get("pluginRoot") if isinstance(data.get("metadata"), dict) else None
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
            info = self.check_plugin(local)
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
            if kind == "codex" and source.get("source") == "local":
                source = source.get("path")
                if not isinstance(source, str):
                    self.error(path, f"{where}.source.path is required for local sources")
                    return None
            else:
                if "source" not in source:
                    self.error(path, f"{where}.source object needs a 'source' type")
                return None
        if not isinstance(source, str):
            self.error(path, f"{where}.source must be a string or an object")
            return None
        if kind == "claude" and isinstance(plugin_root, str) and not source.startswith("./"):
            base = self.check_rel_path(self.root, plugin_root, path, "metadata.pluginRoot")
            return self.check_rel_path(base, "./" + source, path, f"{where}.source") if base else None
        return self.check_rel_path(self.root, source, path, f"{where}.source")

    def check_claude_entry(self, path: Path, where: str, entry: dict, local: Path) -> None:
        manifest = local / ".claude-plugin" / "plugin.json"
        if entry.get("strict") is False and manifest.is_file() and CLAUDE_REPLACING_KEYS & set(entry):
            self.error(path, f"{where}: strict false with component fields conflicts with "
                             f"{manifest.relative_to(self.root).as_posix()}; Claude Code refuses to load it")
        if "version" in entry and manifest.is_file():
            try:
                has_version = "version" in json.loads(manifest.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                has_version = False
            if has_version:
                self.warn(path, f"{where}: version is set in both the entry and the plugin manifest; "
                                "the manifest wins. Set it in one place")
        for key in sorted(COMPONENT_KEYS & set(entry)):
            values = entry[key] if isinstance(entry[key], list) else [entry[key]]
            for value in values:
                if isinstance(value, str):
                    self.check_rel_path(local, value, path, f"{where}.{key}")

    def check_codex_entry(self, path: Path, where: str, entry: dict) -> None:
        policy = entry.get("policy")
        if not isinstance(policy, dict):
            self.warn(path, f"{where}.policy is expected by Codex (installation, authentication)")
        else:
            if policy.get("installation") not in CODEX_INSTALL:
                self.warn(path, f"{where}.policy.installation should be one of {', '.join(sorted(CODEX_INSTALL))}")
            if "authentication" in policy and policy["authentication"] not in CODEX_AUTH:
                self.warn(path, f"{where}.policy.authentication should be one of {', '.join(sorted(CODEX_AUTH))}")
        if not isinstance(entry.get("category"), str):
            self.warn(path, f"{where}.category is expected by Codex")

    # -- entry point -------------------------------------------------------
    def run(self) -> list[dict[str, str]]:
        is_plugin = any((self.root / p).is_file() for p in
                        ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"))
        has_catalog = any((self.root / p).is_file() for p in CATALOGS.values())
        if is_plugin or (not has_catalog and (self.root / "skills").is_dir()):
            self.check_plugin(self.root)
        self.check_catalogs()
        if not self.plugins and not self.catalogs:
            self.error(self.root, "no plugin manifest, skills/ folder, or marketplace catalog found")
        return self.findings


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


def _rel(root: Path, p: Path) -> str:
    try:
        return p.relative_to(root).as_posix() or "."
    except ValueError:
        return str(p)


if __name__ == "__main__":
    sys.exit(main())
