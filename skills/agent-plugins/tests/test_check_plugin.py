"""Tests for scripts/check_plugin.py. Run: python3 -m unittest discover -s tests"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_plugin  # noqa: E402

SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def write(root: Path, files: dict[str, object]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")


def skill(name: str) -> str:
    return f"---\nname: {name}\ndescription: d\n---\n\n# T\n"


def good_plugin(name: str = "release-tools") -> dict[str, object]:
    return {
        "plugin.json": {"$schema": SCHEMA, "name": name, "version": "1.0.0"},
        f"skills/{name}-notes/SKILL.md": skill(f"{name}-notes"),
        "mcp.json": {"$schema": MCP, "mcpServers": {
            "local": {"type": "stdio", "command": "node", "args": ["${PLUGIN_ROOT}/s.js"]},
            "remote": {"type": "streamable-http", "url": "https://example.com/mcp"}}},
        ".claude-plugin/plugin.json": {"name": name, "version": "1.0.0"},
    }


class CheckPluginTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_checker(self, path: Path | None = None) -> list[tuple[str, str]]:
        return [(f["level"], f["message"]) for f in check_plugin.Checker(path or self.root).run()]

    def errors(self, path: Path | None = None) -> list[str]:
        return [m for level, m in self.run_checker(path) if level == "error"]

    def warnings(self, path: Path | None = None) -> list[str]:
        return [m for level, m in self.run_checker(path) if level == "warning"]

    def test_good_dual_format_plugin_is_clean(self) -> None:
        write(self.root, good_plugin())
        self.assertEqual(self.run_checker(), [])

    def test_unknown_schema_and_bad_name(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA.replace("1.0.0", "9.0.0"), "name": "x"}})
        self.assertTrue(any("unknown $schema" in m for m in self.errors()))
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "Bad--Name"}})
        self.assertTrue(any("name 'Bad--Name'" in m for m in self.errors()))

    def test_component_paths_in_core_manifest_warn(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "x", "agents": "./agents"}})
        self.assertTrue(any("component paths are not part" in m for m in self.warnings()))

    def test_author_extra_member_is_error(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "x", "author": {"name": "a", "org": "b"}}})
        self.assertTrue(any("author.org" in m for m in self.errors()))

    def test_legacy_root_manifest_warns(self) -> None:
        write(self.root, {"plugin.json": {"name": "x"}})
        self.assertTrue(any("no $schema" in m for m in self.warnings()))

    def test_mcp_rules(self) -> None:
        files = good_plugin("x")
        files["mcp.json"] = {"$schema": MCP, "mcpServers": {
            "a": {"type": "stdio", "command": "node server.js"},
            "b": {"type": "stdio", "command": "/usr/bin/node", "env": {"PLUGIN_ROOT": "x"}},
            "c": {"type": "streamable-http", "url": "http://example.com/mcp"},
            "d": {"type": "websocket"},
            "e": {"type": "stdio", "command": "node", "cwd": "../up"}}}
        write(self.root, files)
        errors = "\n".join(self.errors())
        for text in ("mcpServers.a.command must be one executable token",
                     "mcpServers.b.command must be a bare name",
                     "mcpServers.b.env must not set PLUGIN_ROOT",
                     "mcpServers.c.url must use https",
                     "mcpServers.d.type",
                     "mcpServers.e.cwd"):
            self.assertIn(text, errors)

    def test_mcp_schema_mismatch(self) -> None:
        files = good_plugin("x")
        files["mcp.json"] = {"mcpServers": {}, "extra": 1}
        write(self.root, files)
        errors = self.errors()
        self.assertTrue(any("$schema must be" in m for m in errors))
        self.assertTrue(any("'extra'" in m for m in errors))

    def test_skill_without_skill_md_and_name_mismatch(self) -> None:
        files = good_plugin("x")
        files["skills/nested/deeper/SKILL.md"] = skill("deeper")
        files["skills/wrong/SKILL.md"] = skill("other")
        write(self.root, files)
        self.assertTrue(any("no SKILL.md directly inside" in m for m in self.warnings()))
        self.assertTrue(any("must equal the folder name 'wrong'" in m for m in self.errors()))

    def test_claude_rules(self) -> None:
        write(self.root, {
            "plugin.json": {"$schema": SCHEMA, "name": "claude-tools"},
            ".claude-plugin/plugin.json": {"name": "claude-tools", "agents": "agents", "mcpServers": "./mcp.json"},
            ".claude-plugin/hooks.json": "{}",
            "mcp.json": {"$schema": MCP, "mcpServers": {}},
        })
        errors = self.errors()
        self.assertTrue(any("reserved by Claude Code" in m for m in errors))
        self.assertTrue(any("must start with './'" in m for m in errors))
        warnings = self.warnings()
        self.assertTrue(any("only manifests belong" in m for m in warnings))
        self.assertTrue(any("points at the Agent Plugins mcp.json" in m for m in warnings))

    def test_name_mismatch_between_manifests(self) -> None:
        files = good_plugin("x")
        files[".claude-plugin/plugin.json"] = {"name": "y"}
        write(self.root, files)
        self.assertTrue(any("name differs between manifests" in m for m in self.errors()))

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_symlink_escaping_root(self) -> None:
        plugin = self.root / "p"
        write(plugin, good_plugin("x"))
        (self.root / "outside").mkdir()
        os.symlink(self.root / "outside", plugin / "skills" / "linked")
        self.assertTrue(any("symlink points outside" in m for m in self.errors(plugin)))

    def test_catalogs_consistency_and_sources(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root / "plugins" / "beta", good_plugin("beta"))
        write(self.root, {
            ".claude-plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"}, "plugins": [
                {"name": "alpha", "source": "./plugins/alpha"},
                {"name": "beta", "source": "./plugins/beta"}]},
            ".github/plugin/marketplace.json": {"name": "example-tools", "plugins": [
                {"name": "alpha", "source": "./plugins/alpha"}]},
            ".agents/plugins/marketplace.json": {"name": "example-tools", "plugins": [
                {"name": "alpha", "source": {"source": "local", "path": "./plugins/alpha"},
                 "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Dev"},
                {"name": "beta", "source": "./plugins/beta",
                 "policy": {"installation": "AVAILABLE"}, "category": "Dev"}]},
        })
        findings = self.run_checker()
        self.assertEqual([m for level, m in findings if level == "error"], [])
        self.assertTrue(any("missing plugins listed in other catalogs: beta" in m for _, m in findings))

    def test_catalog_errors(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root, {".claude-plugin/marketplace.json": {"name": "agent-skills", "plugins": [
            {"name": "renamed", "source": "./plugins/alpha"},
            {"name": "gone", "source": "./plugins/missing"},
            {"name": "up", "source": "../elsewhere"},
            {"name": "remote", "source": {"source": "github", "repo": "o/r"}},
            {"name": "remote", "source": {"repo": "o/r"}}]}})
        errors = "\n".join(self.errors())
        for text in ("reserved by Claude Code", "'owner.name' is required", "differs from the plugin manifest name",
                     "not found", "must not contain '..'", "duplicate plugin name 'remote'",
                     "needs a 'source' type"):
            self.assertIn(text, errors)

    def test_claude_strict_false_conflict_and_double_version(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root, {".claude-plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"},
                          "plugins": [{"name": "alpha", "source": "./plugins/alpha", "strict": False,
                                       "skills": ["./skills/alpha-notes"], "version": "2.0.0"}]}})
        self.assertTrue(any("strict false" in m for m in self.errors()))
        self.assertTrue(any("version is set in both" in m for m in self.warnings()))

    def test_plugin_root_bare_source(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root, {".claude-plugin/marketplace.json": {
            "name": "example-tools", "owner": {"name": "o"}, "metadata": {"pluginRoot": "./plugins"},
            "plugins": [{"name": "alpha", "source": "alpha"}]}})
        self.assertEqual(self.errors(), [])

    def test_codex_entry_warnings(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root, {".agents/plugins/marketplace.json": {"name": "m", "plugins": [
            {"name": "alpha", "source": "./plugins/alpha", "policy": {"installation": "MAYBE"}}]}})
        warnings = "\n".join(self.warnings())
        self.assertIn("policy.installation", warnings)
        self.assertIn("category is expected", warnings)

    def test_empty_folder_and_cli(self) -> None:
        self.assertTrue(any("no plugin manifest" in m for m in self.errors()))
        write(self.root, good_plugin())
        out = io.StringIO()
        with redirect_stdout(out):
            code = check_plugin.main([str(self.root), "--json"])
        self.assertEqual(code, 0)
        report = json.loads(out.getvalue())
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["plugins"][0]["name"], "release-tools")
        self.assertEqual(check_plugin.main([str(self.root / "missing")]), 2)


if __name__ == "__main__":
    unittest.main()
