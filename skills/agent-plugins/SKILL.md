---
name: agent-plugins
description: >-
  Standards for packaging skills, agents, hooks, and MCP servers as agent
  plugins and publishing marketplaces: the open Agent Plugins format, Claude
  Code plugins, and Copilot and Codex extensions. Use when creating, converting,
  or reviewing a plugin.json, marketplace.json, or plugin layout.
---

# Agent plugins

Package agent context so each target harness installs it as one versioned unit, and keep the plugin flavors apart. How to write the skills, agents, or hooks inside a plugin is out of scope; follow any standards the user has for those.

## Library projects only

- Plugins are authored in library projects: repositories whose job is to publish agent context to others. Consumer projects (applications, services) install plugins; they do not author them.
- In a consumer project, do not add a plugin manifest or marketplace unless the user asks. Repository-local context belongs in the harness's own project locations, such as `AGENTS.md` or a skills folder.
- Package as a plugin when components must ship together (a skill with its MCP server or hook), when others install by name from a catalog, or when updates must be versioned. A single skill copied into a skills folder needs no plugin.

## Flavors

There is no single plugin format. Name the flavor every time you write a file, and never mix one flavor's fields into another's manifest.

| Flavor | Marker | Core components | Read by (2026-11) |
| --- | --- | --- | --- |
| Agent Plugins 1.0 (open spec) | Root `plugin.json` with `"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"` | `skills/`, `mcp.json`. Everything else in reverse-domain extension namespaces. | VS Code, Copilot CLI and app, Codex, Cursor, Kiro, others |
| Claude Code | `.claude-plugin/plugin.json` (optional; layout alone also works) | `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, more | Claude Code, claude.ai, Cowork. Copilot CLI and VS Code also read it. |
| Copilot legacy | Root `plugin.json` without `$schema` | Path fields for agents, skills, commands, hooks, MCP, LSP | Copilot CLI, VS Code |
| Codex compatibility | `.codex-plugin/plugin.json` | Fallback for Codex settings when root `extensions.com.openai` is absent | Codex |

Differences that break plugins:

- **Closed vs open manifest.** 1.0 allows only `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`. Component paths, inline MCP, and harness keys are not allowed there. Claude's manifest takes component paths, inline `mcpServers`, `userConfig`, and more.
- **Fixed vs configurable locations.** 1.0 discovers only immediate children of `skills/` and the root `mcp.json`. Claude and Copilot legacy can point at other paths.
- **MCP file.** 1.0: `mcp.json`, with its own `$schema` (same version as `plugin.json`) and a `type` per server. Claude: `.mcp.json` or inline. Do not point one at the other.
- **Root variables.** 1.0: `${PLUGIN_ROOT}` and `${PLUGIN_DATA}`, expanded only in MCP stdio `args`, `env` values, and `cwd`. Claude: `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`, in hooks, MCP, LSP, and more.
- **Format detection.** VS Code and Copilot use 1.0 semantics when the root `plugin.json` has the 1.0 `$schema`, and only then ignore `.claude-plugin/`. Without `$schema`, a root `plugin.json` is read as Copilot legacy.
- **Marketplaces.** 1.0 defines none; each harness reads its own catalog file. See [marketplaces.md](references/marketplaces.md).

## Choosing targets

List the harnesses the plugin must load in, asking if unknown, then pick the layout:

| Targets | Layout |
| --- | --- |
| Any 1.0 client, not Claude Code | 1.0 core only |
| Claude Code only | Claude format only |
| Claude Code and 1.0 clients (default for a public library) | 1.0 core plus `.claude-plugin/plugin.json`, sharing `skills/` |

Put each harness-only component where only that harness reads it: a 1.0 extension namespace (`com.github.copilot/`, `extensions.com.openai`) and Claude's own folders. The same agent or hook usually needs a copy per harness, because frontmatter, tool names, and hook events differ.

## Workflow

1. Confirm the repository is a library. If it is a consumer project, ask before adding plugin files.
2. Record the plugin's purpose and targets wherever the repository keeps feature intent, and list the targets in the plugin's README.
3. Lay out components first, then write manifests, then catalog entries.
4. Validate: run the checker, then each target harness's own validator, then install the plugin locally in every target and confirm each component loads. The commands are in the harness references.

```bash
python3 "<skill-dir>/scripts/check_plugin.py" <plugin-or-repo-root>          # Windows: py -3
python3 "<skill-dir>/scripts/check_plugin.py" <plugin-or-repo-root> --json
```

The checker reads every flavor it finds: manifest fields and names, `skills/` entries, `mcp.json`, component paths, links that escape the plugin root, and catalogs. Errors exit `1`.

## Rules

- **Name** a plugin in lowercase kebab-case, 64 characters or fewer, not starting with `claude-` or `anthropic-`. Use the same name in every manifest and every catalog entry; installs resolve by the catalog entry name.
- **Paths** start with `./`, use forward slashes, stay inside the plugin root, and never contain `..`. Harnesses copy plugins into a cache, so anything outside the root, including symlink targets, is missing after install.
- **State** goes in the plugin data directory (`${PLUGIN_DATA}` or `${CLAUDE_PLUGIN_DATA}`), never under the plugin root. The root is replaced on every update.
- **Secrets** never go in manifests, `env`, or `headers`. Use the harness's sensitive config or auth mechanism (Claude `userConfig` with `sensitive`, Codex `extensions.com.openai.auth`).
- **MCP stdio** `command` is one executable token (a bare name or a `./` path), not a shell string. Put arguments in `args`.
- **Versions**: pick one policy per catalog. Either bump `version` on every release, or omit it everywhere and let harnesses track commits. Never set it in both the manifest and the catalog entry.
- **Freshness**: formats and harness support change monthly. When a behaviour matters, check the dated facts in the references against the linked docs, and record what you verified.

## References

- [agent-plugins-spec.md](references/agent-plugins-spec.md): read when writing a 1.0 manifest, `mcp.json`, or an extension namespace.
- [claude-code.md](references/claude-code.md): read when Claude Code is a target.
- [github-copilot.md](references/github-copilot.md): read when GitHub Copilot (CLI, app, or VS Code) is a target.
- [codex.md](references/codex.md): read when Codex is a target.
- [marketplaces.md](references/marketplaces.md): read when publishing a catalog or serving several harnesses from one repository.
- [library-layout.md](references/library-layout.md): read when adding plugins to a library that already ships loose skills, or when several plugins share components.
