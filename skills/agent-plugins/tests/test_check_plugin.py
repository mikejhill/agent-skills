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
        write(self.root, {"plugin.json": {"$schema": "https://example.com/plugin.schema.json", "name": "x"}})
        self.assertTrue(any("unknown $schema" in m for m in self.errors()))
        write(self.root, {"plugin.json": {"$schema": SCHEMA.replace("1.0.0", "1.1.0"), "name": "x"}})
        self.assertEqual(self.errors(), [])
        self.assertTrue(any("1.1.0 is not implemented by this checker" in m for m in self.warnings()))
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "Bad--Name"}})
        self.assertTrue(any("name 'Bad--Name'" in m for m in self.errors()))

    def test_component_paths_in_core_manifest_warn(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "x", "agents": "./agents"}})
        self.assertTrue(any("component paths are not part" in m for m in self.warnings()))

    def test_author_extra_member_is_error(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "x", "author": {"name": "a", "org": "b"}}})
        self.assertIn("author.org: only name, email, and url are allowed", self.errors())

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
        self.assertTrue(any("resolves outside the root" in m for m in self.errors(plugin)))

    def test_catalogs_consistency_and_sources(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root / "plugins" / "beta", good_plugin("beta"))
        write(self.root, {
            ".claude-plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"}, "plugins": [
                {"name": "alpha", "source": "./plugins/alpha"},
                {"name": "beta", "source": "./plugins/beta"}]},
            ".github/plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"}, "plugins": [
                {"name": "alpha", "source": "plugins/alpha"}]},
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

    def test_round2_mcp_rules(self) -> None:
        files = good_plugin("x")
        files["mcp.json"] = {"$schema": MCP, "mcpServers": {
            "missing": {"type": "stdio", "command": "./bin/missing"},
            "mixed": {"type": "stdio", "command": "node", "url": "https://example.com"},
            "badurl": {"type": "streamable-http", "url": "https://[::1/mcp"},
            "loop": {"type": "streamable-http", "url": "http://127.0.0.2/mcp"},
            "hdr": {"type": "streamable-http", "url": "https://example.com/mcp",
                    "headers": {"X-Tenant": "a", "x-tenant": "b", "bad name": "c"}},
            "nullargs": {"type": "stdio", "command": "node", "args": None},
            "ext": {"type": "stdio", "command": "node", "extensions": {"com.openai": {"auth": {}}}}}}
        write(self.root, files)
        errors = "\n".join(self.errors())
        for text in ("mcpServers.missing.command './bin/missing': not found", "mcpServers.mixed.url: not a stdio field",
                     "mcpServers.badurl.url is malformed", "duplicates another header", "'bad name' is not a valid",
                     "mcpServers.nullargs.args"):
            self.assertIn(text, errors)
        for text in ("mcpServers.loop", "mcpServers.ext"):
            self.assertNotIn(text, errors)

    def test_null_core_fields_are_errors(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "x", "keywords": None, "author": None}})
        errors = self.errors()
        self.assertIn("'keywords' must be an array of strings", errors)
        self.assertIn("'author' must be an object", errors)

    def test_portable_skill_needs_description(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "x"},
                          "skills/a/SKILL.md": "---\nname: a\n---\n"})
        self.assertTrue(any("'description' is required" in m for m in self.errors()))

    def test_manifest_free_claude_plugin(self) -> None:
        write(self.root, {"hooks/hooks.json": "{}", "skills/a/SKILL.md": "---\ndescription: d\n---\n"})
        self.assertEqual(self.errors(), [])

    def test_claude_non_path_forms_and_legacy_paths(self) -> None:
        write(self.root, {"SKILL.md": skill("x"), ".claude-plugin/plugin.json": {
            "name": "x", "skills": ".", "mcpServers": "https://example.com/bundle.mcpb"}})
        self.assertEqual(self.errors(), [])
        legacy = self.root / "legacy"
        write(legacy, {"plugin.json": {"name": "y", "agents": "./agents"}})
        self.assertTrue(any("'./agents': not found" in m for m in self.errors(legacy)))

    def test_codex_extension_paths(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "x",
                                          "extensions": {"com.openai": {"onboardingSkill": "./skills/none/SKILL.md"}}}})
        self.assertTrue(any("onboardingSkill" in m for m in self.errors()))

    def test_remote_sources_and_root_source(self) -> None:
        write(self.root, good_plugin("alpha"))
        write(self.root, {".claude-plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"}, "plugins": [
            {"name": "alpha", "source": "."},
            {"name": "gh", "source": {"source": "github"}},
            {"name": "odd", "source": {"source": "ftp", "url": "x"}}]}})
        errors = "\n".join(self.errors())
        self.assertIn("source.repo is required for github sources", errors)
        self.assertIn("source type 'ftp' is not supported", errors)
        self.assertNotIn("plugins[alpha]", errors)

    def test_plugin_root_rejects_multi_segment(self) -> None:
        write(self.root / "plugins" / "team" / "alpha", good_plugin("alpha"))
        write(self.root, {".claude-plugin/marketplace.json": {
            "name": "example-tools", "owner": {"name": "o"}, "metadata": {"pluginRoot": "./plugins"},
            "plugins": [{"name": "alpha", "source": "team/alpha"}]}})
        self.assertTrue(any("must start with './'" in m for m in self.errors()))

    def test_codex_policy_types_and_metadata_union(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root, {
            ".agents/plugins/marketplace.json": {"name": "m", "plugins": [
                {"name": "alpha", "source": "./plugins/alpha", "version": "1",
                 "policy": {"installation": ["AVAILABLE"]}, "category": "Dev"}]},
            ".claude-plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"}, "plugins": [
                {"name": "alpha", "source": "./plugins/alpha", "version": "2"}]},
            ".github/plugin/marketplace.json": {"name": "m", "owner": {"name": "o"}, "plugins": []}})
        warnings = "\n".join(self.warnings())
        self.assertIn("policy.installation should be", warnings)
        self.assertIn("policy.authentication should be", warnings)
        self.assertIn("alpha: version differs between catalogs", warnings)

    def test_round3_fixes(self) -> None:
        files = good_plugin("x")
        files["skills/rel/SKILL.md"] = "---\nname: rel notes\ndescription: # TODO\n---\n"
        files["skills/ok/SKILL.md"] = "---\nname: 'ok'\ndescription: >-\n  Folded\n  text.\n---\n"
        files["mcp.json"] = {"$schema": MCP, "mcpServers": {
            "cwd": {"type": "stdio", "command": "node", "cwd": "./a\\..\\.."},
            "nl": {"type": "streamable-http", "url": "https://example.com", "headers": {"X-A": "v\n"}},
            "auth": {"type": "stdio", "command": "node", "extensions": {"com.openai": {"auth": {}}}}}}
        files[".claude-plugin/plugin.json"] = {"name": "x", "agents": [42], "skills": False}
        files[".codex-plugin/plugin.json"] = {"name": "x", "onboardingSkill": "./nope/SKILL.md"}
        write(self.root, files)
        errors = "\n".join(self.errors())
        for text in ("name 'rel notes' must equal", "'description' is required", "mcpServers.cwd.cwd",
                     "headers.X-A must be a string without control", "agents: 42 is not a valid value",
                     "skills: False is not a valid value", "onboardingSkill './nope/SKILL.md': not found"):
            self.assertIn(text, errors)
        self.assertNotIn("skills/ok", errors)
        self.assertTrue(any("mcpServers.auth.extensions is a client extension" in m for m in self.warnings()))

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_symlink_loop_is_reported(self) -> None:
        write(self.root, good_plugin("x"))
        os.symlink(self.root / "loop", self.root / "loop")
        self.assertTrue(any("resolves outside" in m for m in self.errors()))

    def test_claude_entry_rules(self) -> None:
        write(self.root / "plugins" / "bare", {"tools/s.json": "{}"})
        write(self.root / "plugins" / "hooky", good_plugin("hooky"))
        write(self.root / "plugins" / "hooky", {"h.json": "{}"})
        write(self.root, {".claude-plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"}, "plugins": [
            {"name": "bare", "source": "./plugins/bare", "mcpServers": "./tools/s.json"},
            {"name": "hooky", "source": "./plugins/hooky", "hooks": "./h.json"}]}})
        errors = "\n".join(self.errors())
        self.assertNotIn("no plugin manifest", errors)
        self.assertIn("accepts only inline hooks", errors)

    def test_copilot_root_catalog_and_owner(self) -> None:
        write(self.root / "plugins" / "alpha", good_plugin("alpha"))
        write(self.root, {"marketplace.json": {"name": "m", "plugins": [{"name": "alpha", "source": "plugins/alpha"}]},
                          ".github/plugin/marketplace.json": {"name": "m", "owner": {"name": "o"}, "plugins": [
                              {"name": "alpha", "source": "./plugins/alpha"}]}})
        self.assertIn("'owner.name' is required", self.errors())
        self.assertTrue(any("Copilot loads one catalog" in m for m in self.warnings()))

    def test_round4_fixes(self) -> None:
        portable = self.root / "portable"
        write(portable, {"plugin.json": {"$schema": SCHEMA, "name": "portable"},
                         "mcp.json": {"$schema": MCP, "mcpServers": {
                             "sp": {"type": "streamable-http", "url": "https://example com/mcp"}}}})
        write(self.root / "withskill", {"plugin.json": {"$schema": SCHEMA, "name": "withskill"},
                                        "skills/Bad_Name/SKILL.md": "---\nname: Bad_Name\ndescription: []\n---\n"})
        write(self.root, {".claude-plugin/marketplace.json": {"name": "example-tools", "owner": {"name": "o"}, "plugins": [
            {"name": "portable", "source": "./portable"},
            {"name": "withskill", "source": "./withskill"},
            {"name": "remote", "source": {"source": "github", "repo": "o/r"}, "hooks": "./hooks.json"}]}})
        errors = "\n".join(self.errors())
        for text in ("Claude Code finds no plugin it can load", "accepts only inline hooks",
                     "url must not contain whitespace", "Agent Skills names are",
                     "'description' is required by Agent Skills and must be a string"):
            self.assertIn(text, errors)

    def test_standalone_openplugin_and_codex_compat(self) -> None:
        legacy = self.root / "legacy"
        write(legacy, {".plugin/plugin.json": {"name": "legacy", "agents": "./custom"}})
        self.assertTrue(any("'./custom': not found" in m for m in self.errors(legacy)))
        codex = self.root / "codex"
        write(codex, {".codex-plugin/plugin.json": {"name": "c", "skills": "./custom-skills", "apps": {},
                                                    "onboardingSkill": []}})
        errors = "\n".join(self.errors(codex))
        for text in ("'./custom-skills': not found", "apps must be a path string", "onboardingSkill must be a path string"):
            self.assertIn(text, errors)

    def test_name_with_trailing_newline(self) -> None:
        write(self.root, {"plugin.json": {"$schema": SCHEMA, "name": "notes\n"},
                          ".claude-plugin/plugin.json": {"name": "notes\n"}})
        errors = "\n".join(self.errors())
        self.assertIn("1-64 of a-z", errors)
        self.assertIn("requires kebab-case", errors)

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
