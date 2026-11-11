# Custom Agents

Custom Agents define specialist assistants with explicit scope, tool restrictions, and constraints for role-specific workflows. Use this reference to create agent files with handoffs, subagent invocation, and controlled tool access.

## Overview

- **Purpose:** Define specialist assistants with explicit scope, tools, and constraints.
- **When to use:** Use for role-specific workflows (planning, research, front-end, etc.).
- **File locations:**
  - Workspace: `.github/agents/` (default for Copilot)
  - Workspace: `.claude/agents/` (Claude Code compatibility — uses different frontmatter format)
  - User-level: `~/.copilot/agents/`
  - Configurable via `chat.agentFilesLocations` VS Code setting
  - File naming: `<name>.agent.md` where `<name>` is descriptive and role-focused
  - Examples: `code-reviewer.agent.md`, `planner.agent.md`, `api-designer.agent.md`
  - Names must clearly indicate the agent's specialized function
  - Must use lowercase and hyphens
- **Selection/activation:** Three modes:
  - **Explicit selection:** User selects the agent from the agent picker in chat
  - **Subagent invocation:** Agents can be automatically invoked via the `runSubagent` tool when `disable-model-invocation: false` (default) and the agent's `description` matches the task
  - **Handoffs:** Agents can trigger workflow transitions to other agents via handoff buttons

## Frontmatter

```yaml
---
name: "Planner"                               # Optional: Defaults to filename
description: "Generate implementation plans"  # Optional: Used for picker and subagent discovery
argument-hint: "feature=..."                  # Optional: Hint text in chat input
tools: ["search", "web"]                      # Optional: Defaults to all user-enabled tools
model: "Claude Sonnet 4"                      # Optional: Overrides user's selected model (string or array)
agents: ["Agent1", "Agent2"]                  # Optional: Restrict allowed subagents (omit=all, []=none)
user-invocable: true                          # Optional: Default true. Whether users can select this agent in the UI
disable-model-invocation: false               # Optional: Default false. If true, prevents subagent invocation
target: "vscode"                              # Optional: "vscode" or "github-copilot" (for cloud coding agent)
hooks:                                        # Optional (Preview): Agent-scoped hooks
  PreToolUse:
    - type: command
      command: "./scripts/validate.sh"
handoffs:                                     # Optional: Workflow transitions
  - label: "Implement Plan"
    agent: "agent"
    prompt: "Implement the plan..."
    model: "Claude Sonnet 4"
    send: false
---
```

All fields are optional:

- `name`: Display name shown in agent picker (defaults to filename if omitted).
- `description`: Brief explanation of agent's purpose. Used for subagent discovery when model invocation is enabled.
- `argument-hint`: User-friendly hint text shown in chat input (e.g., "feature=...").
- `tools`: List of available tools for this agent. If omitted, all user-enabled tools are available.
  - Use `[]` for no tools (conversational only)
  - Common patterns: `["read", "search"]` (read-only), `["read", "edit", "search"]` (no terminal)
  - Also accepts MCP server names (e.g., `"mcp__server-name__tool-name"`) and extension tool identifiers
- `model`: Specific AI model to use (overrides user's selected model). Can be a string or an array for prioritized fallback (e.g., `['Claude Opus 4.5', 'GPT-5.2']` — uses the first available model).
- `agents`: Restrict allowed subagents by name array. Omit for all agents, `[]` for none.
- `user-invocable`: Whether the agent can be selected and invoked by users in the UI. Default is `true`.
- `disable-model-invocation`: If `true`, prevents the agent from being invoked as a subagent. Default is `false`.
- `target`: Environment targeting. Use `"vscode"` (default) for VS Code or `"github-copilot"` for the cloud-based Copilot coding agent.
- `hooks`: (Preview — requires `chat.useCustomAgentHooks`) Agent-scoped hooks that run only when this agent is active. Uses the same event/command structure as workspace hooks.
- `handoffs`: Define sequential workflow transitions with:
  - `label`: Button text shown to user
  - `agent`: Target agent name to switch to
  - `prompt`: Pre-filled prompt text for next agent
  - `model`: Optional model override for the handoff target
  - `send`: Auto-submit flag (true/false). Recommended: false for user review.

> **Deprecated:** The `infer` field has been replaced by the combination of `user-invocable` and `disable-model-invocation`. Do not use `infer` in new agents.

### Controlling Agent Visibility and Invocation

| Configuration                    | In agent picker? | Subagent invocation? | Use Case                                    |
| -------------------------------- | ---------------- | -------------------- | ------------------------------------------- |
| Default (both omitted)           | Yes              | Yes                  | General-purpose agents                      |
| `user-invocable: false`          | No               | Yes                  | Background agents only invoked as subagents |
| `disable-model-invocation: true` | Yes              | No                   | Agents only used via direct user selection  |
| Both set                         | No               | No                   | Disabled agents                             |

## Tool Aliases

| Alias     | Purpose                           |
| --------- | --------------------------------- |
| `execute` | Run terminal commands             |
| `read`    | Read file contents                |
| `edit`    | Edit files                        |
| `search`  | Search files or text              |
| `agent`   | Invoke custom agents as subagents |
| `web`     | Fetch URLs and web search         |
| `todo`    | Manage task lists                 |

## Body Layout

Role → Capabilities → Tools → Constraints → Handoffs/Subagent criteria → Examples.

## Examples

```markdown
---
name: planner
description: Generate implementation plans without modifying code.
tools: ["search", "web"]
handoffs:
  - label: Start Implementation
    agent: agent
    prompt: Implement the plan outlined above step by step.
    send: false
  - label: Review Plan
    agent: code-reviewer
    prompt: Review this implementation plan for potential issues.
    send: false
---

## Role

Research and generate detailed implementation plans without editing files.

## Capabilities

- Analyze requirements and existing codebase
- Create step-by-step implementation plans
- Identify dependencies and potential risks

## Tools

- search, fetch (read-only operations)

## Constraints

- DO NOT modify any files
- DO NOT run code or tests

## Handoffs

After generating a plan, users can:

- Click "Start Implementation" to switch to the default agent with the implementation prompt pre-filled
- Click "Review Plan" to switch to code-reviewer agent for plan validation

## Examples

Task: Plan a new authentication feature
Output: Detailed plan with steps, files to modify, and testing approach
Next: User clicks "Start Implementation" to begin coding
```

## How Handoffs Work

- After the agent completes its response, handoff buttons appear below the output
- Clicking a handoff button switches to the target agent and pre-fills the prompt
- If `send: true`, the prompt auto-submits; if `send: false` (recommended), user can review/edit first

## Anti-patterns

- Swiss-army agents with too many tools trying to do everything
- Vague descriptions that don't guide delegation ("A helpful agent")
- Role confusion where description doesn't match body persona
- Circular handoffs (A → B → A) without clear progress criteria

## Validation Checklist

- Stored in a recognized agents directory (`.github/agents/` or configured location)
- File naming: `*.agent.md`
- All frontmatter fields are optional
- Configure `user-invocable` and `disable-model-invocation` to control UI visibility and subagent behavior
- Do not use the deprecated `infer` field — use `user-invocable` and `disable-model-invocation` instead
- Use minimal tool sets matched to the agent's specific role
- Define clear constraints on what the agent should NOT do
- Handoffs are defined when workflow needs staged steps
- Avoid circular handoffs without progress criteria
