# AGENTS.md

AGENTS.md provides tool-agnostic instructions for all agents in the workspace, designed to work across GitHub Copilot, Claude Code, and other AI assistants. Use this reference to create and configure AGENTS.md files.

## Overview

- **Purpose:** Provide custom instructions intended for all agents in the workspace. Intended to be tool-agnostic (GitHub Copilot, Claude Code, etc.).
- **When to use:** Use when multiple agents share the same baseline rules and constraints.
- **File locations:**
  - Path: `AGENTS.md` (workspace root) or nested in subfolders
  - Claude Code equivalent: `CLAUDE.md` (workspace root or `.claude/CLAUDE.md`)
  - User-level: `~/.copilot/AGENTS.md`, `~/.claude/CLAUDE.md`
  - Fixed filename with no variation
  - VS Code settings: `chat.useAgentsMdFile` (enable/disable), `chat.useClaudeMdFile` (enable/disable), `chat.useNestedAgentsMdFiles` (experimental — enables nested files)
- **Selection/activation:**
  - Automatically applied to all chat requests
  - When multiple `AGENTS.md` files exist, only the closest to the active file is used
  - For monorepos, this allows folder-specific overrides
  - Use `chat.useCustomizationsInParentRepositories` for monorepo support with parent directory scanning
- **Important:** Both copilot-instructions.md and AGENTS.md can coexist. Use copilot-instructions.md for Copilot-specific guidance and AGENTS.md for tool-agnostic rules. Do not duplicate the same rules in both files.

## Frontmatter

None. Do not use YAML frontmatter.

## Body Layout

Structure with headings and imperative rules. Keep rules concise, tool-agnostic, and applicable to any AI assistant.

- Use `#` or `##` headings to organize by concern (e.g., coding standards, testing, documentation)
- State rules as imperative commands, not suggestions
- Do not reference tool-specific features (e.g., VS Code settings, Claude-specific syntax)
- Link to external docs rather than embedding full content

**AGENTS.md hierarchy:** For monorepos, the closest AGENTS.md in the directory tree takes precedence, allowing folder-specific overrides. A nested AGENTS.md replaces (not extends) the parent file.

## Examples

### Basic workspace-wide rules

```markdown
# Agent-wide Instructions

- Do not modify files without confirmation
- Prefer reading existing code before proposing changes
- Use type hints for all Python function signatures
- Write tests for all new public functions
```

### Monorepo with folder-specific overrides

Root `AGENTS.md`:

```markdown
# Project Standards

- Use English for all code comments and documentation
- Follow semantic versioning for all packages
- Run tests before committing changes
```

`packages/api/AGENTS.md` (overrides root for files in this folder):

```markdown
# API Package Standards

- Use Express.js middleware patterns for route handlers
- Return structured JSON error responses with status codes
- Log all API errors with request ID and timestamp
```

## Anti-patterns

- Duplicating rules already in copilot-instructions.md (split concerns instead)
- Including tool-specific syntax or features (defeats cross-tool purpose)
- Overly verbose instructions that exceed the scope of workspace-wide guidance
- Using AGENTS.md as a feature registry or documentation index

## Validation Checklist

- Stored at workspace root as `AGENTS.md` and/or optional nested files in subfolders
- No YAML frontmatter
- Rules are tool-agnostic (no Copilot-specific or Claude-specific syntax)
- Contains agent-wide instructions, not a discoverable registry
- If copilot-instructions.md also exists, ensure no duplicate rules between the two files
- If using nested AGENTS.md files, enable `chat.useNestedAgentsMdFiles` in VS Code settings
