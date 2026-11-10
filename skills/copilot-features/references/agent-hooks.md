# Agent Hooks

Agent Hooks execute custom shell commands at specific agent lifecycle points with deterministic, guaranteed outcomes. Use this reference to create hooks that enforce security policies, run quality checks, or inject context.

## Overview

- **Purpose:** Execute custom shell commands at key agent lifecycle points with guaranteed outcomes.
- **When to use:** Use for deterministic automation that must enforce security policies, run code quality checks, create audit trails, or inject context.
- **File locations:**
  - Workspace: `.github/hooks/*.json` (shared with team) — **preferred for Copilot**
  - Workspace: `.claude/settings.json` (Claude Code compatibility — project hooks)
  - Workspace: `.claude/settings.local.json` (Claude Code compatibility — local hooks, gitignored)
  - User-level: `~/.copilot/hooks/*.json` (personal hooks, apply to all workspaces)
  - Agent-scoped: `hooks` field in `.agent.md` frontmatter (Preview — requires `chat.useCustomAgentHooks`)
  - Configurable via `chat.hookFilesLocations` VS Code setting
- **Selection/activation:** Hooks fire automatically at specific lifecycle events. No manual invocation required.
- **Format compatibility:** Uses the same format as Claude Code and Copilot CLI for cross-tool compatibility.

## Key Differences from Instructions

Unlike instructions or custom prompts that guide agent behavior, hooks:

- Execute your code deterministically with guaranteed outcomes
- Can block tool execution before it happens (PreToolUse)
- Run at specific lifecycle points regardless of agent prompting
- Communicate via JSON stdin/stdout
- Use exit codes to control execution flow

## Hook Events

VS Code supports eight hook lifecycle events:

| Event                | Fires When                        | Common Uses                                                     |
| -------------------- | --------------------------------- | --------------------------------------------------------------- |
| **SessionStart**     | New session begins                | Initialize resources, inject project context, validate setup    |
| **UserPromptSubmit** | User submits a prompt             | Audit requests, inject context based on prompt                  |
| **PreToolUse**       | Before agent invokes any tool     | Block dangerous operations, require approval, modify tool input |
| **PostToolUse**      | After tool completes successfully | Run formatters/linters, log results, trigger follow-up actions  |
| **PreCompact**       | Before context compaction         | Export state, save important context                            |
| **SubagentStart**    | Subagent spawns                   | Track nested agents, initialize subagent resources              |
| **SubagentStop**     | Subagent completes                | Aggregate results, cleanup resources                            |
| **Stop**             | Agent session ends                | Generate reports, cleanup, send notifications                   |

## Configuration Format

Hooks are defined in JSON files with the following structure:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "./scripts/validate-tool.sh",
        "timeout": 15
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "command": "npx prettier --write \"$TOOL_INPUT_FILE_PATH\""
      }
    ]
  }
}
```

## Hook Properties

Each hook entry requires:

| Property    | Type   | Required | Description                                     |
| ----------- | ------ | -------- | ----------------------------------------------- |
| **type**    | string | Yes      | Must be `"command"`                             |
| **command** | string | Yes\*    | Default command (cross-platform)                |
| **windows** | string | No       | Windows-specific command override               |
| **linux**   | string | No       | Linux-specific command override                 |
| **osx**     | string | No       | macOS-specific command override                 |
| **cwd**     | string | No       | Working directory (relative to repository root) |
| **env**     | object | No       | Additional environment variables                |
| **timeout** | number | No       | Timeout in seconds (default: 30)                |

\*Either `command` or an OS-specific property must be provided.

## Environment Variables

Hook commands have access to these environment variables:

| Variable                  | Description                                            |
| ------------------------- | ------------------------------------------------------ |
| `$TOOL_INPUT_FILE_PATH`   | File path from tool input (when tool operates on a file) |
| `$CLAUDE_PROJECT_DIR`     | Project root directory (Claude Code compatibility)     |

Use workspace-relative paths in `.github/hooks/` for Copilot. Use `"$CLAUDE_PROJECT_DIR"` for project-relative scripts in Claude Code contexts. Additional variables can be defined via the `env` property in hook configuration.

## OS-Specific Commands

Define different commands per operating system:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "./scripts/format.sh",
        "windows": "powershell -File scripts\\format.ps1",
        "linux": "./scripts/format-linux.sh",
        "osx": "./scripts/format-mac.sh"
      }
    ]
  }
}
```

VS Code selects the command based on the extension host platform (which may differ from your local OS in remote development scenarios).

## Input Format (stdin)

All hooks receive JSON via stdin with common fields:

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-identifier",
  "hookEventName": "PreToolUse",
  "transcript_path": "/path/to/transcript.json"
}
```

Event-specific fields are added to this base object. See Hook Event Details below.

## Output Format (stdout)

Hooks can return JSON via stdout to influence behavior:

```json
{
  "continue": true,
  "stopReason": "Security policy violation",
  "systemMessage": "Operation blocked by security hook"
}
```

| Field             | Type    | Description                                         |
| ----------------- | ------- | --------------------------------------------------- |
| **continue**      | boolean | Set to `false` to stop processing (default: `true`) |
| **stopReason**    | string  | Message shown when `continue` is `false`            |
| **systemMessage** | string  | Warning message shown to user                       |

## Exit Codes

Hook exit codes determine execution flow:

| Code      | Meaning              | Effect                                                     |
| --------- | -------------------- | ---------------------------------------------------------- |
| **0**     | Success              | Parse stdout for JSON, proceed with action                 |
| **2**     | Blocking error       | Ignore stdout, feed stderr to agent as error, block action |
| **Other** | Non-blocking warning | Show warning to user, continue processing                  |

## Hook Event Details

### PreToolUse

Fires before agent invokes any tool.

**Additional Input:**

```json
{
  "tool_name": "editFiles",
  "tool_input": { "files": ["src/main.ts"] },
  "tool_use_id": "tool-123"
}
```

**Decision Control (hookSpecificOutput):**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked",
    "updatedInput": { "files": ["src/safe.ts"] },
    "additionalContext": "Current environment: production"
  }
}
```

| Field                        | Values                       | Description                    |
| ---------------------------- | ---------------------------- | ------------------------------ |
| **permissionDecision**       | `"allow"`, `"deny"`, `"ask"` | Controls tool approval         |
| **permissionDecisionReason** | string                       | Reason shown to user           |
| **updatedInput**             | object                       | Modified tool input (optional) |
| **additionalContext**        | string                       | Extra context for model        |

**Permission priority:** When multiple hooks run, most restrictive wins: `deny` > `ask` > `allow`.

### PostToolUse

Fires after tool completes successfully.

**Additional Input:**

```json
{
  "tool_name": "editFiles",
  "tool_input": { "files": ["src/main.ts"] },
  "tool_use_id": "tool-123",
  "tool_response": "File edited successfully"
}
```

**Decision Control:**

```json
{
  "decision": "block",
  "reason": "Post-processing validation failed",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "File has lint errors that need fixing"
  }
}
```

### UserPromptSubmit

Fires when user submits a prompt.

**Additional Input:**

```json
{
  "prompt": "Write a function to calculate factorial"
}
```

**Uses common output format only.**

### SessionStart

Fires when new session begins.

**Additional Input:**

```json
{
  "source": "new"
}
```

**Decision Control (hookSpecificOutput):**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Project: my-app v2.1.0 | Branch: main"
  }
}
```

### Stop

Fires when agent session ends.

**Additional Input:**

```json
{
  "stop_hook_active": false
}
```

**Decision Control:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "decision": "block",
    "reason": "Run test suite before finishing"
  }
}
```

**Note:** Check `stop_hook_active` to prevent infinite loops.

### SubagentStart

Fires when subagent spawns.

**Additional Input:**

```json
{
  "agent_id": "subagent-456",
  "agent_type": "Plan"
}
```

**Decision Control (hookSpecificOutput):**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Follow project coding guidelines"
  }
}
```

### SubagentStop

Fires when subagent completes.

**Additional Input:**

```json
{
  "agent_id": "subagent-456",
  "agent_type": "Plan",
  "stop_hook_active": false
}
```

**Decision Control:**

```json
{
  "decision": "block",
  "reason": "Verify subagent results before completing"
}
```

### PreCompact

Fires before context compaction.

**Additional Input:**

```json
{
  "trigger": "auto"
}
```

**Uses common output format only.**

## Configuration with /hooks Command

Use `/hooks` slash command in chat for interactive configuration:

1. Type `/hooks` in chat and press Enter
2. Select hook event type
3. Choose existing hook to edit or add new one
4. Select or create hook configuration file

The command opens the file with cursor positioned for editing.

## Example Use Cases

### Block Dangerous Commands

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "./scripts/block-dangerous.sh"
      }
    ]
  }
}
```

**Script (`./scripts/block-dangerous.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ "$COMMAND" == *"rm -rf"* ]]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Destructive rm command blocked"}}'
  exit 0
fi

exit 0
```

### Auto-Format After Edits

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "npx prettier --write \"$TOOL_INPUT_FILE_PATH\"",
        "timeout": 60
      }
    ]
  }
}
```

### Inject Project Context

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "./scripts/inject-context.sh"
      }
    ]
  }
}
```

**Script:**

```bash
#!/bin/bash
BRANCH=$(git branch --show-current)
VERSION=$(cat package.json | jq -r '.version')
NODE_VERSION=$(node --version)

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Project: my-app v$VERSION | Branch: $BRANCH | Node: $NODE_VERSION"
  }
}
EOF
```

## Safety Considerations

**CRITICAL:** Hooks execute shell commands with your full user permissions.

- Review all hook scripts before using
- Validate and sanitize all input data
- Quote shell variables: use `"$VAR"` not `$VAR`
- Block path traversal: check for `..` in paths
- Use absolute paths with `"$CLAUDE_PROJECT_DIR"` for project-relative scripts (Claude Code compatibility) — use workspace-relative paths in `.github/hooks/` for Copilot
- Skip sensitive files: avoid `.env`, `.git/`, keys

**VS Code mitigations:**

- `chat.tools.edits.autoApprove` setting prevents agent from editing hook scripts without approval
- Use in combination with terminal tool controls and auto-approve allow-lists

## Troubleshooting

### View Hook Diagnostics

1. Right-click in Chat view → **Diagnostics**
2. Look for hooks section for loaded hooks and errors

### View Hook Output

1. Open **Output** panel
2. Select **GitHub Copilot Chat Hooks** from channel list

### Common Issues

| Issue              | Solution                                                                             |
| ------------------ | ------------------------------------------------------------------------------------ |
| Hook not executing | Verify file in `.github/hooks/` with `.json` extension. Check `type` is `"command"`. |
| Permission denied  | Ensure script has execute permissions (`chmod +x script.sh`)                         |
| Timeout errors     | Increase `timeout` value or optimize script                                          |
| JSON parse errors  | Verify script outputs valid JSON. Use `jq` to construct output.                      |

## Anti-patterns

- Using hooks for guiding behavior instead of instructions (hooks are for deterministic automation)
- Blocking all operations instead of specific dangerous ones
- Not validating input from agent before using in shell commands
- Hardcoding secrets in hook scripts instead of using environment variables
- Ignoring `stop_hook_active` flag in Stop/SubagentStop hooks (causes infinite loops)

## Validation Checklist

- Stored in correct location (`.github/hooks/*.json`, user-level `~/.copilot/hooks/`, or settings files)
- `type` property set to `"command"`
- Command exists and is executable
- Script outputs valid JSON when needed
- Exit codes used correctly (0 = success, 2 = blocking error)
- Input validation present in scripts
- Timeout set to match expected duration of long-running operations
- Security review completed for all scripts
