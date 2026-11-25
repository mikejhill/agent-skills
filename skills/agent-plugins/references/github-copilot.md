# GitHub Copilot plugins

Copilot CLI, the Copilot app, the Copilot SDK, and VS Code support Agent Plugins 1.0 (GA 2026-08-12) and still load older formats. Docs: <https://docs.github.com/en/copilot/reference/plugin-and-marketplace-reference>, <https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference>.

## Format detection

| Format | Marker | Root variable |
| --- | --- | --- |
| Agent Plugins 1.0 (Copilot CLI also recognizes a 1.1.0 schema) | Root `plugin.json` with the canonical `$schema` | `${PLUGIN_ROOT}` |
| Claude | `.claude-plugin/plugin.json` | `${CLAUDE_PLUGIN_ROOT}` |
| Copilot (default when nothing else matches) | Root `plugin.json` without `$schema` | `${PLUGIN_ROOT}` or `${CLAUDE_PLUGIN_ROOT}` |
| Legacy OpenPlugin | `.plugin/plugin.json` | `${PLUGIN_ROOT}` |

The root 1.0 `$schema` wins. Do not ship a Copilot-legacy root `plugin.json` next to a 1.0 one; there is only one root file.

## Components in a 1.0 package

| Component | Location |
| --- | --- |
| Skills, MCP | Core: `skills/`, `mcp.json` |
| Custom agents | `com.github.copilot/agents/<name>.agent.md` |
| Slash commands | `com.github.copilot/commands/` |
| Rules | `com.github.copilot/rules/` |
| Hooks | `com.github.copilot/hooks/hooks.json` |
| LSP | `com.github.copilot/lsp.json` (CLI) |
| Automations (VS Code) | `automations/*.automation.md`; override with `extensions["com.github.copilot"].automations.paths` |

- VS Code reads `com.github.copilot` and ignores other namespaces. Support for each extension component varies between VS Code, the CLI, and the app; test in each.
- Legacy Copilot packages declare component paths in `plugin.json` (`agents`, `skills`, `commands`, `hooks`, `mcpServers`, `lspServers`) and default to `agents/`, `skills/`, `hooks.json` or `hooks/hooks.json`, `.mcp.json`, `lsp.json`. Migrate them to 1.0 when touched.

## Marketplace

- Catalog: `.github/plugin/marketplace.json` or a root `marketplace.json`; keep only one. Copilot CLI also reads a Claude `.claude-plugin/marketplace.json`.
- Top level: `name`, `owner` (object with `name`), `metadata`, `plugins[]`.
- Entries: `name`, `description`, `version`, `source` (a relative path, with or without `./`, or an object with `source: "url"`, `url`, `ref`). A marketplace feed itself cannot be pinned to a ref.
- Default marketplaces include `github/awesome-copilot`.
- Enterprise policy keys in managed settings: `enabledPlugins`, `extraKnownMarketplaces`, `strictKnownMarketplaces`, `allowManagedHooksOnly`.

## Install and test

```bash
copilot plugin install ./<plugin>                 # local folder
copilot plugin install <owner>/<repo>:<subdir>    # plugin in a repository subfolder
copilot plugin marketplace add <owner>/<repo>
copilot plugin install <name>@<marketplace>
copilot plugin list
```

- In a session: `/plugin list`, `/agent`, `/skills list`.
- VS Code: install from the Agent Plugins view or `@agentPlugins` in Extensions. VS Code caches feeds and can hide a feed whose catalog is invalid; debug catalogs with the CLI first.
- Verify the setting names your VS Code version uses for extra marketplaces and local plugin paths in its docs; they changed during the preview.
