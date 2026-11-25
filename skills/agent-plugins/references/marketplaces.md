# Marketplaces

A marketplace is a catalog file that lists plugins and where to fetch them. Agent Plugins 1.0 defines no catalog, so each harness reads its own (2026-11):

| Harness | Catalog path (from the marketplace root) | Also reads |
| --- | --- | --- |
| Claude Code | `.claude-plugin/marketplace.json` | — |
| GitHub Copilot | `.github/plugin/marketplace.json` (also `.plugin/` or root `marketplace.json`) | `.claude-plugin/marketplace.json` (CLI) |
| Codex | `.agents/plugins/marketplace.json` | `.claude-plugin/marketplace.json` |

## Which catalogs to ship

- Ship the native catalog for every target harness. Do not rely on another harness reading the Claude catalog: field support differs (Codex wants `policy` and `category`; Copilot ignores Claude source types it does not know), and VS Code support for it is unconfirmed.
- Keep the plugin set, names, descriptions, and versions identical across catalogs. Generate the others from one source when there are more than a few plugins. The checker reports differences.
- The marketplace root is the folder that holds the catalog folder, usually the repository root. Relative sources resolve from there and start with `./`.

## Claude Code catalog

```json
{
  "name": "example-tools",
  "owner": { "name": "Example Maintainer" },
  "description": "Release and review tooling.",
  "plugins": [
    { "name": "release-tools", "source": "./plugins/release-tools", "description": "Release checklists." },
    { "name": "lint-hooks", "source": { "source": "github", "repo": "example/lint-hooks", "ref": "v2" } }
  ]
}
```

- Required: `name`, `owner.name`, `plugins[]` with `name` and `source`. Optional: `description`, `version`, `metadata.pluginRoot` (base folder for bare-name sources), `renames`, `forceRemoveDeletedPlugins`.
- Entry `hooks` must be inline objects; put hook files in the plugin itself.
- Source types: `./` path, `github` (`repo`, `ref`, `sha`), `url` (git URL), `git-subdir` (`url`, `path`), `npm`, `archive` (HTTPS zip with `sha256`), `command`. Only object sources work when the catalog itself is added by URL.
- `strict` decides how the entry combines with `.claude-plugin/plugin.json`:
  - No manifest in the plugin: the entry is the manifest, at either strictness.
  - Manifest exists, `strict: true` (default): the manifest is authoritative; entry `commands`, `agents`, `skills`, and `outputStyles` are appended, and entry `mcpServers`, `lspServers`, and `userConfig` are ignored.
  - Manifest exists, `strict: false`: any component field in the entry fails the load, even when the manifest itself declares no components.
  - To publish a subset of a shared `skills/` folder, use an entry with a `skills` list and no per-plugin manifest.
- Reserved marketplace names include `agent-skills`, `claude-plugins-official`, `anthropic-plugins`, and any `claudeai-` prefix. Name the catalog after the publisher or the collection.
- Users install `<entry-name>@<marketplace-name>`. Keep the entry name equal to the manifest name.

## Versioning and updates

| Policy | How | Effect |
| --- | --- | --- |
| Release versions | Bump `version` in the plugin manifest on every release | Users update only when the string changes. Forgetting a bump hides the change. |
| Track commits | Omit `version` everywhere | Harnesses that derive versions from commits update on every push to the source ref. |

- Set `version` in one place. Claude warns when manifest and entry both set it, and the manifest wins.
- Pin external sources with `ref` or `sha` when stability matters more than freshness.
- To rename a plugin, keep the old entry name resolvable where the harness supports it (Claude `renames`), and say so in the release notes.

## Trust

- Catalogs and plugins run code on users' machines (hooks, MCP stdio servers, `bin/`). Review third-party sources before listing them, and pin them.
- Harnesses offer managed allowlists (`strictKnownMarketplaces`) and blocklists. Document the catalog's source URL so administrators can allow it.
