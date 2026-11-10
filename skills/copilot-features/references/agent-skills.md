# Agent Skills

Agent Skills provide specialized, reusable capabilities that load on demand when requests match the skill description. Agent Skills follow the [Agent Skills open standard](https://agentskills.io) and are portable across VS Code, Copilot CLI, and the Copilot coding agent. Use this reference to create skill folders with bundled scripts, templates, and reference documentation.

## Overview

- **Purpose:** Provide specialized, reusable capabilities with optional scripts and resources.
- **When to use:** Use for task-specific workflows that should load on demand. Prefer skills over prompt files for new work due to broader tool support and bundled asset capabilities.
- **File locations:**
  - Workspace: `.github/skills/<name>/` (default for Copilot)
  - Workspace: `.claude/skills/<name>/` (Claude Code compatibility)
  - Workspace: `.agents/skills/<name>/` (tool-agnostic convention)
  - User-level: `~/.copilot/skills/<name>/`, `~/.claude/skills/<name>/`, `~/.agents/skills/<name>/`
  - Configurable via `chat.agentSkillsLocations` VS Code setting
  - Main file: `SKILL.md` (required)
  - Naming: `<name>` must be lowercase, alphanumeric and hyphens only
  - Max 64 characters, no consecutive hyphens, no leading/trailing hyphens
  - Folder name must match the `name` field in frontmatter
  - Examples: `jest-test-generation`, `api-scaffolding`, `security-audit`
  - Avoid generic names like "testing" or "utilities"
- **Selection/activation:** Skills can be activated in two ways:
  - **Automatic:** Auto-selected when user request matches the frontmatter `description`
  - **Manual:** Invoked via slash commands in chat (e.g., `/skill-name additional context`)
  - **CRITICAL:** Only `name` and `description` are used for discovery—the description is the ONLY text that determines automatic loading.
  - By default, skills appear in the slash command menu and can auto-load. Use `user-invocable` and `disable-model-invocation` frontmatter fields to control this behavior.

## Folder Structure

```text
.github/skills/<skill-name>/
├── SKILL.md           # Required (name must match folder)
├── scripts/           # Executable code
├── references/        # Docs loaded as needed
└── assets/            # Templates, boilerplate
```

## Frontmatter

### Standard Fields (Open Standard)

These fields are defined by the [Agent Skills spec](https://agentskills.io) and work across all compatible tools:

```yaml
---
name: skill-name              # Required: Lowercase alphanumeric + hyphens, max 64 chars, must match folder name
description: "Use when..."    # Required: State capability and when to use. Max 1024 chars. Drives auto-activation.
license: "MIT"                # Optional: SPDX license identifier
compatibility:                # Optional: Tool compatibility metadata
  - "copilot"
  - "claude"
metadata:                     # Optional: Arbitrary key-value pairs for tooling
  version: "1.0.0"
  author: "team-name"
---
```

### VS Code-Specific Fields

These fields extend the standard and are recognized only by VS Code:

```yaml
---
argument-hint: "[test file] [options]"  # Optional: Hint shown in chat input when invoked as slash command
user-invocable: true                    # Optional: Controls if skill appears in slash-command menu (default: true)
disable-model-invocation: false         # Optional: Prevents auto-loading, requires slash-command invocation (default: false)
allowed-tools: ["read", "search"]       # Experimental: Restrict tools available to the skill
---
```

**Required fields:**

- `name`: Lowercase, hyphen-separated identifier matching folder name. Max 64 characters, alphanumeric and hyphens only, no consecutive hyphens, no leading/trailing hyphens.
- `description`: Drives automatic activation. State what the skill does and when to use it. Max 1024 characters.

**Optional standard fields:**

- `license`: SPDX license identifier for the skill
- `compatibility`: Array of tool identifiers this skill is compatible with
- `metadata`: Arbitrary key-value pairs for tooling or organizational metadata

**Optional VS Code fields:**

- `argument-hint`: User-friendly hint text shown in chat input when skill is invoked as a slash command (e.g., "\[test file] \[options]", "for the login page")
- `user-invocable`: Set to `false` to hide skill from the slash command menu while allowing automatic loading (default: `true`)
- `disable-model-invocation`: Set to `true` to prevent automatic loading and require explicit slash command invocation (default: `false`)
- `allowed-tools`: Experimental. Restrict which tools are available when the skill is active.

## Description Field

This is the ONLY text used for skill activation. Include:

- What the skill does (capabilities)
- When to use it (trigger scenarios)
- Key technologies or patterns involved
- Be specific to avoid false matches

## Body Layout

Include:

- What the skill accomplishes
- Step-by-step procedures
- A **Related Files** index listing supporting files and what each file is used for
- Examples

### Related Files Index

If the skill includes supporting files (`scripts/`, `references/`, `assets/`), include a section like this in `SKILL.md`:

```markdown
## Related Files

- `references/api-spec.md`: API contract and field constraints used by this skill.
- `scripts/generate-tests.js`: Generates baseline test cases before manual refinement.
- `assets/component-template.tsx`: Starter template used when scaffolding new components.
```

Keep descriptions concise and action-oriented.

## Bundled Assets

Skills can include additional files in the same directory:

- Scripts, templates, checklists, or reference data
- Reference using relative paths: `[template](./template.js)` or `[checklist](./checklist.md)`
- Keep main SKILL.md file under 500 lines; move lengthy content to separate files
- Keep file references one level deep from SKILL.md for optimal loading
- Organize with clear file naming (e.g., `scripts/test.js`, `references/api-spec.md`, `assets/template.ts`)

## Progressive Loading

Skills load in stages to optimize token usage:

1. **Discovery** (~100 tokens): Agent reads `name` and `description`
2. **Instructions** (<5000 tokens): Loads SKILL.md body when relevant
3. **Resources**: Additional files load only when referenced

**Token budget guidance:** Keep SKILL.md under 500 lines and ~5000 tokens total. The instructions stage loads the body content; move lengthy reference material to separate files. Dense prose averages 30–50 tokens per line, but SKILL.md files typically contain headings, lists, code blocks, and whitespace that average closer to 10–15 tokens per line — a 500-line file with typical structure falls within the 5000-token budget.

## Using Skills as Slash Commands

Skills are available as slash commands in chat alongside prompt files. Type `/` in chat to see all available skills.

### Invocation Methods

1. **Automatic loading:** Agent loads skill when request matches `description`
2. **Manual invocation:** Type `/skill-name` in chat, optionally followed by context (e.g., `/webapp-testing for the login page`)

### Controlling Skill Visibility and Loading

Use frontmatter fields to control how skills are accessed:

| Configuration                    | In the slash command menu? | Auto-loads? | Use Case                                            |
| -------------------------------- | -------------------------- | ----------- | --------------------------------------------------- |
| Default (both omitted)           | Yes                        | Yes         | General-purpose skills                              |
| `user-invocable: false`          | No                         | Yes         | Background knowledge skills that load when relevant |
| `disable-model-invocation: true` | Yes                        | No          | Skills you only want to run on demand               |
| Both set                         | No                         | No          | Disabled skills                                     |

**Important:** Only **one** slash command can be used at a time. You cannot use slash commands to manually select multiple skills simultaneously.

### Argument Hints

Use `argument-hint` to guide users when they invoke your skill:

```yaml
---
name: github-actions-debugging
description: Debug GitHub Actions workflow failures
argument-hint: PR #[number] or workflow name
---
```

When users type `/github-actions-debugging`, the hint "PR #\[number] or workflow name" appears in the chat input field.

## Description Examples

- "Use when generating REST APIs from OpenAPI specs with validation and error handling."
- "Use when writing PowerShell scripts that require registry modifications and idempotent checks."
- "Use when creating React components that must follow MUI v5 patterns."

## Examples

### Example 1: Auto-loading skill

```markdown
---
name: jest-test-generation
description: Use when generating Jest tests for JavaScript functions with mocking and edge case coverage.
---

# Skill Instructions

## Procedure

1. Identify inputs, outputs, and dependencies
2. Define success, edge, and error cases
3. Mock external dependencies
4. Write assertions with clear expectations
5. Add descriptive test names

## Example

Input: Function that fetches user data
Output: Tests for success, network error, and empty response
```

### Example 2: Slash-command-only skill with argument hint

```markdown
---
name: github-actions-debugging
description: Debug GitHub Actions workflow failures by analyzing logs and suggesting fixes
argument-hint: PR #[number] or workflow name
disable-model-invocation: true
---

# Skill Instructions

## Procedure

1. Retrieve workflow run logs
2. Identify failure points in the logs
3. Analyze error messages and stack traces
4. Suggest specific fixes based on common patterns
5. Provide corrected workflow YAML if needed

## Example

Input: `/github-actions-debugging PR #42`
Output: Analysis of workflow failures with suggested fixes
```

## Anti-patterns

- Vague descriptions that don't enable discovery (e.g., "A helpful skill")
- Monolithic SKILL.md with everything in one file instead of using reference files
- Name mismatch between folder name and frontmatter `name` field
- Missing step-by-step procedures (descriptions without actionable guidance)
- Missing a Related Files list when the skill depends on additional files
- Setting both `user-invocable: false` and `disable-model-invocation: true` (disables skill entirely)
- Using generic `argument-hint` that doesn't help users understand what to provide

## Troubleshooting

If a skill doesn't auto-load when expected, check the Diagnostics view in VS Code (right-click in Chat → **Diagnostics**) to see which skills are loaded and which `description` fields matched. Verify the skill is in a recognized location and that `disable-model-invocation` is not set to `true`.

## Validation Checklist

- Stored in a recognized skills directory (`.github/skills/<name>/`, `.claude/skills/<name>/`, or configured location)
- Folder name must match `name` field in frontmatter
- `name`: max 64 characters, alphanumeric and hyphens only, no consecutive or leading/trailing hyphens
- `description`: max 1024 characters, specific enough to avoid false matches
- Required fields: `name` and `description` in frontmatter are specific
- Optional fields used correctly: `argument-hint`, `user-invocable`, `disable-model-invocation`, `license`, `compatibility`, `metadata`
- Keep SKILL.md under 500 lines / ~5000 tokens; use reference files for lengthy content
- File references should be one level deep from SKILL.md
- Include a `## Related Files` section in SKILL.md when supporting files exist, with one-line descriptions for each file
- Body includes what skill accomplishes, when to use, procedures, and examples
- If using visibility controls, not both set to disable (which disables skill entirely)
