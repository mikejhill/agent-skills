# Claude Code plugins

Claude Code reads only its own format. It is not an Agent Plugins client (2026-11) and ignores a root 1.0 `plugin.json`. Docs: <https://code.claude.com/docs/en/plugins-reference>, <https://code.claude.com/docs/en/plugins/marketplace-reference>.

## Layout

```text
<plugin>/
├── .claude-plugin/plugin.json   # optional manifest; nothing else goes in this folder
├── skills/<name>/SKILL.md
├── commands/*.md
├── agents/*.md
├── hooks/hooks.json
├── .mcp.json
├── .lsp.json
├── output-styles/
├── bin/                         # added to PATH; claude.ai and Cowork refuse plugins that have it
└── settings.json                # only `agent` and `subagentStatusLine` apply
```

## Manifest

- Only `name` is required: kebab-case; no spaces, `@`, `:`, or path separators. Components are namespaced `<plugin>:<component>`.
- Reserved: names starting `claude-`, `anthropic-`, `anthropics-`, `cc-plugin-`, and `claude`, `anthropic`, `claude-code`, among others.
- Optional: `displayName`, `version`, `description`, `author` (object, `name` required), `homepage`, `repository`, `license`, `keywords`, `dependencies`, `userConfig`, `defaultEnabled`, and component keys `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`, `outputStyles`.
- Unknown top-level keys are stripped with a warning.
- Component keys: `skills`, `hooks`, `mcpServers`, `lspServers` add to the default location; `commands`, `agents`, `outputStyles` replace it.
- Paths start with `./`, stay inside the root, and contain no `..` or backslashes.
- `version` pins users to that copy until the string changes. Omit it to track commits.

## Variables and config

- `${CLAUDE_PLUGIN_ROOT}`: the installed version folder, replaced on each update. `${CLAUDE_PLUGIN_DATA}`: persistent data, kept across updates.
- `userConfig`: options prompted at enable time (`type`, `title`, `description`, `sensitive`, ...). Sensitive values go to the OS secure store. Reference values as `${user_config.KEY}` in MCP, LSP, exec-form hook `args`, skills, and agents; hooks also get `CLAUDE_PLUGIN_OPTION_<KEY>`.
- In shell-form hook commands, quote the root: `"\"${CLAUDE_PLUGIN_ROOT}\"/scripts/run.sh"`. Prefer exec-form hooks with `args`.

## Coexisting with a 1.0 plugin

- Keep Claude-only keys in `.claude-plugin/plugin.json`. Put the shared metadata (`name`, `version`, `description`, `author`, `license`) in both manifests with identical values.
- Claude finds the shared `skills/` by default; no `skills` key is needed.
- MCP: declare servers in `.mcp.json` or inline in `.claude-plugin/plugin.json` with `${CLAUDE_PLUGIN_ROOT}`. Do not reuse the 1.0 `mcp.json`; its schema and variables differ.
- Claude-format folders at the root (`agents/`, `commands/`) are ignored by Copilot and VS Code when the root manifest carries the 1.0 `$schema`. Without it, Copilot reads the package as Claude or Copilot format and loads them.
- Hooks are the exception: Codex discovers `hooks/hooks.json` by default. Put Claude-only hooks at a non-default path, such as `claude/hooks.json`, and reference it from the `hooks` key in `.claude-plugin/plugin.json`. Give Codex its own hooks through `extensions["com.openai"].hooks`.

## Validate and test

```bash
claude plugin validate <plugin-or-marketplace> --strict   # warnings fail; validates a catalog without opening plugin files
claude --plugin-dir <plugin>                               # load for one session
claude plugin marketplace add ./<marketplace-root>
claude plugin install <name>@<marketplace>
```

Run `/reload-plugins` in a session to pick up edits. Validate each plugin folder as well as the catalog.

## Marketplace

`.claude-plugin/marketplace.json` at the marketplace root. See [marketplaces.md](marketplaces.md) for fields, source types, and strict mode.
