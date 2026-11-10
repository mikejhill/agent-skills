---
name: copilot-features
description: Use when creating or modifying any GitHub Copilot customization features, including custom instructions, AGENTS.md, agent skills, prompt files, custom agents, or agent hooks. Helps select the correct feature type and create, review, or modify it for optimal performance.
---

# Skill Instructions

## Overview

GitHub Copilot provides a set of customization features that tailor how the AI assistant behaves. These features let you define coding standards, create reusable workflows, build specialized tools, and control how guidance is applied across your codebase. Each feature serves a distinct purpose—from always-on workspace rules to on-demand skills and lifecycle automation—and choosing the right one depends on your specific needs. Some features (Agent Skills and Agent Hooks) follow cross-tool standards and work across VS Code, Copilot CLI, and Claude Code; others are VS Code-specific.

This skill helps you:

- Understand each feature type and when to use it
- Select the correct feature based on your requirements
- Format and structure each feature type correctly
- Navigate detailed documentation for implementation

## How to Use this Skill

**CRITICAL**: The current file is just an overview, but the files linked have much more information. Once a feature type is selected, you **MUST** read the associated linked file for much more information.

Use the Feature Reference for quick lookup, the Feature Selection Guide to make informed choices, and the linked documentation for comprehensive implementation guidance.

See also the **Global Rules** section for important rules which apply when creating or editing all features.

## Feature Reference

| Feature                 | Usage                            | Selection/Activation                                                    | Primary Location                                | Documentation                                              |
| ----------------------- | -------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------- |
| **Custom Instructions** | Always-on coding standards       | Auto-applied                                                            | `.github/copilot-instructions.md`               | [Custom Instructions](./references/custom-instructions.md) |
| **Instructions Files**  | File- or task-specific rules     | Auto-applied by `applyTo`, on-demand by `description`, or manual attach | `.github/instructions/*.instructions.md`        | [Instructions Files](./references/instructions-files.md)   |
| **AGENTS.md**           | Global agent instructions        | Auto-applied                                                            | `AGENTS.md` (workspace root or subfolders)      | [AGENTS.md](./references/agents-md.md)                     |
| **Agent Skills**        | On-demand capabilities           | Auto-loaded by `description` match or slash commands                    | `.github/skills/<name>/SKILL.md`                | [Agent Skills](./references/agent-skills.md)               |
| **Prompt Files**        | Explicit, repeatable tasks       | Run explicitly by user via slash commands                               | `.github/prompts/<name>.prompt.md`              | [Prompt Files](./references/prompt-files.md)               |
| **Custom Agents**       | Role-specific tools+instructions | Selected by user or subagent invocation                                 | `.github/agents/<name>.agent.md`                | [Custom Agents](./references/custom-agents.md)             |
| **Agent Hooks**         | Lifecycle automation             | Auto-fires at lifecycle events                                          | `.github/hooks/*.json`, `.claude/settings.json` | [Agent Hooks](./references/agent-hooks.md)                 |

> **Locations are configurable.** Each feature type has a default workspace location shown above, but VS Code also supports user-level locations (e.g., `~/.copilot/skills/`) and configurable search paths via `chat.*Locations` settings. See each reference file for the full list of supported locations.

### Feature Purposes

- **Custom Instructions** – Define workspace-wide rules, standards, and conventions that are automatically applied to every chat request. Use for guidance that affects all development work.
- **Instructions Files** – Define scoped instructions for specific files, languages, or folders that activate based on file patterns or semantic task matching. Use when rules should apply only to certain contexts. (VS Code only)
- **AGENTS.md** – Provide custom instructions intended for all agents in the workspace, designed to be tool-agnostic and work across multiple AI assistants (GitHub Copilot, Claude Code, etc.).
- **Agent Skills** – Provide specialized, reusable capabilities with optional bundled assets (scripts, templates, checklists) that load on demand. Skills follow the [Agent Skills open standard](https://agentskills.io) and are portable across VS Code, Copilot CLI, and the Copilot coding agent. Prefer skills over prompt files for new work due to broader tool support.
- **Prompt Files** – Provide explicit, reusable prompts for repeatable tasks that users invoke through slash commands or the command palette. Useful for lightweight, single-task prompts in VS Code. For portable or multi-file workflows, prefer Agent Skills instead. (VS Code only)
- **Custom Agents** – Define specialist assistants with explicit scope, tool restrictions, and constraints for role-specific workflows like planning, code review, or research. Supports both VS Code and the Copilot coding agent (via the `target` field).
- **Agent Hooks** – Execute custom shell commands deterministically at specific agent lifecycle points (SessionStart, PreToolUse, PostToolUse, etc.) to enforce security policies, automate quality checks, create audit trails, or inject context. Hook entry schema is shared across Copilot and Claude Code; container file formats differ.

### Cross-Tool Compatibility

| Feature              | VS Code | Copilot CLI | Copilot Coding Agent | Claude Code      |
| -------------------- | ------- | ----------- | -------------------- | ---------------- |
| Custom Instructions  | ✓       | —           | ✓                    | Own format       |
| Instructions Files   | ✓       | —           | —                    | `.claude/rules/` |
| AGENTS.md            | ✓       | ✓           | ✓                    | `CLAUDE.md`      |
| Agent Skills         | ✓       | ✓           | ✓                    | ✓                |
| Prompt Files         | ✓       | —           | —                    | —                |
| Custom Agents        | ✓       | —           | ✓                    | Own format       |
| Agent Hooks          | ✓       | ✓           | ✓                    | ✓                |

Agent Skills are the most portable feature type. When a feature could be implemented as either a skill or a prompt, prefer a skill for cross-tool compatibility.

## Feature Selection Guide

### When to Use Each Feature

Use this flow to quickly choose the right feature type:

| Condition                                                    | Feature Type                                          |
| ------------------------------------------------------------ | ----------------------------------------------------- |
| Applies to every request in the workspace                    | Custom instructions or AGENTS.md                      |
| Applies only to specific files/folders                       | Instructions files (with `applyTo`)                   |
| Loads on-demand when task is relevant                        | Instructions files (with `description`), Agent Skills |
| Single focused task with parameterized inputs                | Prompt files                                          |
| Needs bundled assets (scripts/templates)                     | Agent Skills                                          |
| Needs tool restrictions or context isolation                 | Custom agents                                         |
| Multi-stage workflow with handoffs                           | Custom agents                                         |
| Requires deterministic automation with guaranteed outcomes   | Agent Hooks                                           |
| Requires blocking/modifying tool execution before it happens | Agent Hooks (PreToolUse event)                        |

**Important:** Only **one** slash command can be used at a time. This includes skills and prompt files invoked via slash commands, so you cannot manually select multiple skills/prompts in a single request.

### Comparing Across Features

Use these criteria when choosing between similar feature types:

#### Instructions Files vs Agent Skills

- Does this apply to _most_ work in a domain? → Instructions Files
- Does this apply to _specific_ tasks or workflows? → Agent Skills
- Example: "Always use type hints in Python" → Instructions. "Generate Jest tests with mocks" → Skill.

#### Agent Skills vs Prompt Files

- Multi-step workflow with bundled assets (scripts, templates)? → Agent Skills
- Single focused task with parameterized inputs, VS Code only? → Prompt Files
- Needs portability across tools (CLI, coding agent, Claude Code)? → Agent Skills
- Example: "Security audit with checklist + scripts" → Skill. "Generate API route from method + path" → Prompt.

#### Agent Skills vs Custom Agents

- Same capabilities needed for all steps? → Agent Skills
- Need context isolation (subagent returns single output)? → Custom Agents
- Need different tool restrictions per stage? → Custom Agents
- Example: "Generate tests following team standards" → Skill. "Plan feature (read-only) → Implement → Review (different tools each stage)" → Custom Agents.

#### Custom Instructions vs AGENTS.md

- GitHub Copilot-specific standards? → Custom instructions
- Tool-agnostic rules for multiple AI assistants? → AGENTS.md
- Both can coexist. Use custom instructions for Copilot-specific guidance and AGENTS.md for cross-tool rules. Do not duplicate the same rules in both files.

#### Instructions/Skills vs Agent Hooks

- Need to guide agent behavior? → Instructions or Skills
- Need guaranteed deterministic execution? → Agent Hooks
- Need to block operations before they execute? → Agent Hooks (PreToolUse)
- Need to run code at specific lifecycle points? → Agent Hooks
- Example: "Always validate inputs" → Instructions. "Run linter after every file edit" → Hook.

## Global Rules

### Naming

- Use lowercase, hyphen-separated names for variable-name features (skills, prompts, agents, instructions files).
- Skill and agent names: max 64 characters, alphanumeric and hyphens only, no consecutive hyphens, no leading/trailing hyphens.
- Description fields: max 1024 characters. Keep descriptions concise and specific.
- Avoid generic names (e.g., "testing", "instructions", "standards").
- Use descriptive, action-oriented names that indicate purpose or capability (e.g., `jest-test-generation`, `generate-api-route`, `code-reviewer`).
- Fixed-name features (custom instructions, AGENTS.md) have specific filenames; no variation needed.

### Generation Commands

VS Code provides commands to scaffold features interactively:

- `/create-skill` — Create a new agent skill
- `/create-agent` — Create a new custom agent
- `/create-prompt` — Create a new prompt file
- `/create-instruction` — Create a new instructions file
- `/create-hook` — Create a new agent hook
- `/init` — Initialize workspace customizations (creates `copilot-instructions.md`)

### Other Rules

- For Agent Skills, the `description` is the only text used for automatic activation. It must state capability and when to use it.
- For Prompt Files and Custom Agents, the `description` is UI metadata; make it specific and task-focused.
- For Custom Instructions and AGENTS.md, do not use YAML frontmatter.
- Include one concrete example per feature type.

For detailed guidance on phrasing rules, constraints, and instructions, reference the [writing-ai-instructions](../writing-ai-instructions/SKILL.md) skill.

### Intent Files

Intent files (`INTENT.md` or `<name>.intent.md`) record the operator's goals
and decision history for a feature. They enable feature regeneration,
maintenance, and quality assessment over time.

- Create an intent file when the operator provides goals for a new or existing
  feature.
- When iterating on a feature, append to the intent file's Log section.
- Do NOT include intent files in a skill's frontmatter `references` list.
- See [Intent Files](./references/intent-files.md) for the format
  specification and agent behavior rules.

## Feature Interaction & Precedence

When multiple features activate simultaneously with overlapping guidance:

- **Most specific wins.** Instructions files with `applyTo` targeting specific files override broader custom instructions or AGENTS.md guidance.
- **Explicit over automatic.** User-invoked features (prompt files, slash-command skills) take precedence over auto-applied features.
- **Later context wins.** When features at the same specificity level conflict, the most recently attached or loaded context generally takes precedence. Note: load order for auto-applied features is not user-controllable, so minimize conflicts rather than relying on ordering.
- **Hooks are independent.** Agent hooks execute deterministically regardless of other features. Hook output does not conflict with instruction-based guidance — hooks control execution, instructions control reasoning.
- **Scope hierarchy.** Features exist at three scope levels — organization, workspace, and user — which may overlap. Workspace features generally take precedence over user-level defaults, and organization-level features apply across all repositories.

Minimize conflicts by keeping each feature focused on a distinct concern. Do not duplicate the same rule across multiple features.

## Validation Checklist

- Name is lowercase and hyphen-separated (skills, prompts, agents)
- File path matches feature type
- Required frontmatter fields are present per feature type
- Description uses "Use when..." pattern (for skills and on-demand instructions)
- No banned vague language in content ("appropriate", "reasonable", "consider", "might")
- Examples are included
- See feature-specific validation checklists in each reference file
