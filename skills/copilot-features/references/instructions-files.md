# Instructions Files

Instructions Files enable scoped guidance for specific files, languages, or folders. Use this reference to create instruction files with pattern-based or semantic activation.

## Overview

- **Purpose:** Define scoped instructions for specific files, languages, or folders.
- **When to use:** Use when rules should apply only to matching files or tasks.
- **File locations:**
  - Workspace: `.github/instructions/` (default for Copilot)
  - User-level: `~/.copilot/instructions/` (personal defaults, synced via Settings Sync)
  - Configurable via `chat.instructionsFilesLocations` VS Code setting
  - Subdirectories are scanned recursively
  - File naming: `<name>.instructions.md` where `<name>` is descriptive and domain-specific
  - Examples: `python-standards.instructions.md`, `api-guidelines.instructions.md`, `react-patterns.instructions.md`
  - Must use lowercase and hyphens
  - Claude Code equivalent: `.claude/rules/` directory (uses `paths` property instead of `applyTo`)
- **Selection/activation:** Three modes:
  - **On-demand** (`description`): Agent detects task relevance (task-based: migrations, refactoring, API work)
  - **Explicit** (`applyTo`): Files matching glob in context (file-based: language standards, framework rules)
  - **Manual**: User attaches via "Add Context" (ad-hoc attachment)
  - Note: `applyTo` triggers when creating or modifying matching files, not for read-only operations

## Frontmatter

```yaml
---
name: "Display Name" # Optional: Defaults to filename
description: "Use when..." # Optional: Enables on-demand semantic activation
applyTo: "**/*.py" # Optional: Glob pattern for explicit file matching
---
```

All fields are optional:

- `name`: Display name shown in UI when file is attached or referenced (defaults to filename if omitted).
- `description`: Enables on-demand semantic activation when request matches. Use "Use when..." pattern for clarity.
  - Can be combined with `applyTo` for dual activation: pattern-based AND semantic.
  - When used alone (without `applyTo`), enables pure semantic matching.
  - Include trigger scenarios and key technologies for better discovery.
- `applyTo`: Glob pattern(s) for explicit auto-application to matching files.
  - Single pattern: `"**/*.py"`
  - Multiple patterns (OR logic): `["src/**", "lib/**"]` or `["**/*.ts", "**/*.tsx"]`

## Body Layout

Organize by concern with `##` headings. State rules as imperative commands. Keep rules short, specific, and testable. Include one example per major rule.

## Examples

### Pattern-based

```markdown
---
applyTo: "**/*.py"
---

# Python Standards

- Use type hints for all public functions
- Prefer pathlib over os.path
```

### Semantic On-demand

```markdown
---
name: API Guidelines
description: Use when designing or implementing REST APIs to ensure consistent error handling and versioning.
---

# API Standards

- All endpoints must return structured error responses
- Use semantic versioning in URL paths (/v1/, /v2/)
- Include rate limit headers in responses
```

## Anti-patterns

- Vague descriptions that don't enable discovery (e.g., "Helpful coding tips")
- Using `applyTo: "**"` with content only relevant to specific files (use custom instructions or AGENTS.md for truly global rules, or narrow the glob pattern)
- Duplicating documentation instead of linking
- Mixing multiple concerns in one file (testing + API design + styling)

## Validation Checklist

- Stored in a recognized instructions directory (`.github/instructions/` or configured location)
- File naming: `*.instructions.md`
- `applyTo` enables explicit pattern-based activation
- `description` enables on-demand semantic activation (use "Use when..." pattern)
- Both can be combined for dual activation modes
- If neither is provided, file requires manual attachment
