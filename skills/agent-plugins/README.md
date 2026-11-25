# agent-plugins

Standards for packaging agent context as installable plugins and publishing them in marketplaces, across the open Agent Plugins 1.0 format, Claude Code's plugin format, and harness extensions for GitHub Copilot and Codex. Includes a checker for manifests and catalogs.

## Use

Loads automatically when an agent creates, converts, or reviews a plugin or marketplace. Meant for library repositories that publish agent context; most application repositories never need it. Examples:

- "Package the release skills in this library as a plugin for Claude Code and Copilot."
- "Add a marketplace so Codex users can install our plugins."
- "Convert this Claude plugin to Agent Plugins 1.0."

Run the checker on a plugin folder or a marketplace root. `<skill-dir>` is the folder holding this skill's `SKILL.md`.

```bash
python3 <skill-dir>/scripts/check_plugin.py path/to/plugin-or-repo    # Windows: py -3
python3 <skill-dir>/scripts/check_plugin.py path/to/plugin-or-repo --json
```

## Requirements

- Python 3.9+ for the checker (stdlib only). It reads files and never fetches anything.
- Each target harness's CLI, for its own validation and local install tests.

## Results

The agent writes plugin manifests, `mcp.json`, and catalog files in the library repository. The checker prints findings and exits `1` on errors.

## Notes

- Plugin formats and harness support change often. Facts are dated (last checked 2026-11-25) and link to the source docs; verify anything critical before relying on it.
- Codex marketplace details came partly from summaries of its docs and are marked for verification.
