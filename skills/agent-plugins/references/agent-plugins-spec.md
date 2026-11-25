# Agent Plugins 1.0

The open, harness-neutral plugin format. Spec: <https://agent-plugins.org/specification> (1.0.0, published 2026-08-06, independently governed; maintainers from Amazon, Anysphere, Google, Microsoft, OpenAI, and Vercel). Clients: <https://agent-plugins.org/compatible-clients>.

## Layout

```text
<plugin>/
├── plugin.json            # required
├── skills/<name>/SKILL.md # optional; immediate children only, no recursion
├── mcp.json               # optional
└── <reverse.domain>/      # optional client-owned files, e.g. com.github.copilot/
```

Plugins are plain directories, not archives.

## plugin.json

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "release-tools",
  "version": "1.2.0",
  "description": "Release checklists and a changelog MCP server.",
  "author": { "name": "Example Maintainer", "url": "https://example.com" },
  "repository": "https://github.com/example/release-tools",
  "license": "MIT",
  "keywords": ["release", "changelog"],
  "extensions": { "com.github.copilot": {} }
}
```

| Field | Rule |
| --- | --- |
| `$schema` | Required, exact canonical URL. It selects the validation rules; clients never fetch it. A missing or unknown value rejects the plugin. |
| `name` | Required. 1-64 characters of `a-z`, `0-9`, `-`, `.`; alphanumeric first and last; no `--` or `..`. Avoid `.` if Claude Code is also a target. |
| `version` | String; SemVer recommended. Drives update checks and cache freshness. |
| `author` | Object with only `name`, `email`, `url`. Any other member rejects the plugin. |
| `license` | SPDX recommended. |
| `extensions` | Object keyed by reverse-domain namespace; each value an object. |

- Any other top-level field is reported and ignored. There are no component path fields: the locations are fixed.
- Type errors in the closed fields reject the whole plugin. Metadata is checked by JSON type only.

## mcp.json

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "changelog": {
      "type": "stdio",
      "command": "node",
      "args": ["${PLUGIN_ROOT}/server/index.js"],
      "env": { "CACHE_DIR": "${PLUGIN_DATA}/cache" }
    },
    "docs": { "type": "streamable-http", "url": "https://docs.example.com/mcp" }
  }
}
```

- `$schema` must name the same spec version as `plugin.json`, or MCP is disabled for that plugin.
- No other top-level fields. MCP may not be declared anywhere else.
- `type` is `stdio`, `streamable-http`, or `sse` (deprecated; optional for clients, and Codex does not list it). Prefer `streamable-http` for remote servers.
- `stdio`: `command` (required, one token: a bare name or `./` path), `args`, `env`, `cwd`. `env` must not set `PLUGIN_ROOT` or `PLUGIN_DATA`.
- `streamable-http` and `sse`: `url` (absolute; HTTPS unless loopback; no userinfo or fragment), `headers`.
- No OAuth or credential fields in 1.0. Never embed secrets; use a client extension's auth mechanism. Server entries may carry an `extensions` object for client-specific settings (Codex reads `extensions["com.openai"].auth` there). Any other field outside the selected transport makes clients skip the server.

## Variables

- `${PLUGIN_ROOT}`: absolute plugin root. `${PLUGIN_DATA}`: writable, per-install directory kept across updates.
- Expanded only in stdio `args` items, `env` values, and `cwd`. Not in `command`, `url`, `headers`, or `env` keys. Single pass; unknown placeholders stay literal.
- `cwd` is `./...`, `${PLUGIN_ROOT}[/...]`, or `${PLUGIN_DATA}[/...]`. It defaults to the plugin root.

## Extensions

- Manifest data: `extensions.<namespace>`. Files: a top-level folder named exactly `<namespace>/`.
- Clients ignore namespaces they do not implement, without validating them. Content in one is not portable.
- Known namespaces (2026-11): `com.github.copilot` (agents, commands, rules, hooks, LSP, automations) and `com.openai` (Codex apps, hooks, interface, auth). Check each harness's reference for the contents.

## Not in 1.0

Catalogs and marketplaces, install and update flows, signing, provenance, permissions, sandboxing, and dependencies are client-owned or out of scope. Agents, commands, hooks, and rules are extensions, not core components; no new core type is committed. New core types need a concrete cross-client need and implementer support.
