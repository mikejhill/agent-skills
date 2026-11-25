# Codex plugins

Codex reads Agent Plugins 1.0 and keeps OpenAI-only settings in the `com.openai` extension. Docs: <https://developers.openai.com/plugins/build/plugins>. Several details below came from summaries of that page; verify them before relying on them, and record what you verified.

## Manifest

- Portable entry point: root `plugin.json` (1.0). OpenAI-only settings go in `extensions["com.openai"]`:

| Key | Use |
| --- | --- |
| `interface` | Display metadata: `displayName`, `shortDescription`, `longDescription`, `developerName`, `category`, `capabilities`, `websiteURL`, `privacyPolicyURL`, `termsOfServiceURL`, `defaultPrompt`, `brandColor`, `composerIcon`, `logo` |
| `apps` | Path to an `.app.json` mapping registered apps to MCP servers |
| `hooks` | Path, paths, or inline hook objects. Replaces default discovery of `hooks/hooks.json`. |
| `onboardingSkill` | Path to a packaged `SKILL.md` run after install |

- `.codex-plugin/plugin.json` is the older Codex manifest. Codex uses it only when the root manifest has no `extensions.com.openai`. Do not create one for new plugins; remove it when migrating, or keep it identical in name and version.
- Skills: `skills/<name>/SKILL.md`. MCP: root `mcp.json`, with `type` per server. Codex lists `stdio` and `streamable-http`, not `sse`.
- MCP authentication (OAuth or API keys) goes on the server entry in `mcp.json`, as `mcpServers.<name>.extensions["com.openai"].auth`, not in `plugin.json`. Other clients ignore that namespace.
- Plugins with hooks work when installed manually but are not eligible for the public directory (2026-11).

## Marketplace

- Repository catalog: `.agents/plugins/marketplace.json`. Personal catalog: `~/.agents/plugins/marketplace.json`. Codex also reads `.claude-plugin/marketplace.json`.
- Top level: `name`, optional `interface.displayName`, `plugins[]`.
- Entry: `name`, `source`, `policy`, `category`.
  - `source`: a `./` path string, or an object: `{ "source": "local", "path": "./plugins/x" }`, `url` (plugin at a repository root), `git-subdir` (`url`, `path`, `ref` or `sha`), or `npm` (`package`, optional `version`, `registry`; install scripts do not run).
  - `policy.installation`: `AVAILABLE`, `INSTALLED_BY_DEFAULT`, or `NOT_AVAILABLE`. `policy.authentication`: `ON_INSTALL` or `ON_FIRST_USE`.
- Relative paths resolve from the marketplace root and start with `./`.

## Install and test

```bash
codex plugin marketplace add ./<marketplace-root>
codex plugin marketplace add <owner>/<repo> --ref main
codex plugin marketplace add https://github.com/<owner>/<repo>.git --sparse .agents/plugins
codex plugin marketplace list
codex plugin marketplace upgrade [<name>]
```

Adding a marketplace only registers the catalog. Then test the plugin itself: open the plugin browser (`/plugins` in the CLI, or Plugins in the app), choose the local marketplace, install the entry, start a new session, and exercise one bundled skill and one MCP tool.

Installed plugins are cached under `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`; local plugins use `local` as the version.
