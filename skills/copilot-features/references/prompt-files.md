# Prompt Files

Prompt Files provide explicit, reusable prompts for repeatable tasks that users invoke through slash commands or the command palette. Use this reference to create prompt files with parameterized inputs and consistent execution. For portable, multi-file workflows, prefer Agent Skills instead.

## Overview

- **Purpose:** Provide explicit, reusable prompts for repeatable tasks.
- **When to use:** Use for lightweight, single-task prompts in VS Code. For portable workflows or tasks needing bundled assets, prefer Agent Skills.
- **File locations:**
  - Workspace: `.github/prompts/` (default for Copilot)
  - User-level: stored in VS Code user data, synced via Settings Sync
  - Configurable via `chat.promptFilesLocations` VS Code setting
  - File naming: `<name>.prompt.md` where `<name>` is descriptive and task-focused
  - Examples: `generate-api-route.prompt.md`, `review-security.prompt.md`, `scaffold-component.prompt.md`
  - Must use lowercase and hyphens
- **Selection/activation:** Prompt files are run explicitly by the user:
  - **Chat:** Type `/` and select prompt from list
  - **Command Palette:** Run `Chat: Run Prompt...`
  - **Editor:** Open prompt file and click the play button
- **VS Code only.** Prompt files are not recognized by Copilot CLI, the Copilot coding agent, or Claude Code. Claude Code has no direct equivalent to prompt files. For cross-tool compatibility, use Agent Skills.

## Frontmatter

```yaml
---
name: "generate-api-route"           # Optional: Defaults to filename
description: "Generate an Express route..." # Optional: Shown in prompt picker
argument-hint: "Enter method and path..."   # Optional: Hint text in chat input
agent: "agent"                       # Optional: ask, edit, agent, plan, or custom agent name
tools: ["search", "fetch"]           # Optional: Tool aliases, MCP servers, extensions
model: "Claude Sonnet 4"            # Optional: Overrides user's selected model
---
```

All fields are optional:

- `name`: Prompt name shown after typing `/` in chat (defaults to filename if omitted)
- `description`: Brief explanation of what the prompt does (shown in prompt picker)
- `argument-hint`: User-friendly hint text shown in chat input to guide usage (e.g., "Enter feature name", "Specify file path")
- `agent`: Which agent mode runs the prompt:
  - `ask` — Answer questions without making changes
  - `edit` — Apply edits to files in the editor
  - `agent` — Full agent mode with tool access (default)
  - `plan` — Generate an implementation plan
  - Custom agent name — Delegates to a specific custom agent
- `tools`: List of tools available when running this prompt. See [Custom Agents Tool Aliases](./custom-agents.md#tool-aliases) for built-in alias list. Also accepts MCP server names and extension tool identifiers. When specified, overrides the agent's default tool list.
- `model`: Specific AI model to use (overrides user's selected model)

## File References and Variables

Reference workspace files using Markdown links with relative paths:

```markdown
Review the API spec at [api-spec](../docs/api-spec.md) and generate routes.
```

Reference agent tools using the `#tool:` syntax:

```markdown
Use #tool:search to find existing route handlers before generating new ones.
```

For user input, use the `${input:variableName}` syntax:

```markdown
Generate a ${input:httpMethod} handler for the ${input:routePath} endpoint.
```

## Body Layout

Input → Output → Steps → Example.

## Examples

```markdown
---
name: generate-api-route
description: Generate an Express route with validation, error handling, and JSDoc.
argument-hint: Enter HTTP method and path (e.g., POST /users)
---

# Generate Express API Route

## Input

- HTTP method
- Route path
- Business logic summary

## Output

A TypeScript Express route with validation and error handling.

## Steps

1. Validate inputs
2. Implement handler
3. Add error handling
4. Add JSDoc

## Example

Input: POST /users with name and email
Output: Route handler with validation and database insert
```

## Anti-patterns

- Multi-task prompts trying to do too much ("create and test and deploy")
- Vague descriptions that don't help users understand when to use the prompt
- Including many tools when the task only needs search or file access

## Validation Checklist

- Stored in a recognized prompts directory (`.github/prompts/` or configured location)
- File naming: `*.prompt.md`
- All frontmatter fields are optional
- `agent` field uses a valid mode: `ask`, `edit`, `agent`, `plan`, or a custom agent name
- File references use Markdown link syntax with relative paths
- Tool references use `#tool:<tool-name>` syntax
- User input variables use `${input:variableName}` syntax
