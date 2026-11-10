# Custom Instructions

Custom Instructions define workspace-wide rules, standards, and conventions that apply to every chat request. Use this reference to create and configure the `copilot-instructions.md` file for your workspace.

## Overview

- **Purpose:** Define workspace-wide rules, standards, and conventions.
- **When to use:** Use for guidance that should apply to every chat request in the workspace.
- **File locations:**
  - Workspace: `.github/copilot-instructions.md` (default, fixed filename)
  - Organization-level: Configured via GitHub organization settings (applies across all repos)
  - User-level: `~/.copilot/instructions/` (personal defaults, see Instructions Files reference)
  - For tool-agnostic instructions, use AGENTS.md instead
- **Selection/activation:** Automatically applied to all chat requests in the workspace.
- **VS Code only.** This specific file format is for GitHub Copilot. For cross-tool instructions, use AGENTS.md. Claude Code uses `CLAUDE.md` for the equivalent feature.

## Frontmatter

None. Do not use YAML frontmatter.

## Body Layout

Use headings, imperative rules, and examples. Keep concise—link to detailed docs rather than embedding full content.

### Core Principles

- **Minimal by default:** Only include what's relevant to every task
- **Link, don't embed:** Reference docs instead of copying content
- **Keep current:** Update when practices change

## Examples

````markdown
# React Component Standards

## Naming

- Use PascalCase for component names
- Match file names to component names

## Hooks

- DO NOT call hooks conditionally
- Extract complex hook logic into custom hooks

## Example

```tsx
export const UserProfile = ({ userId }) => {
  const [user, setUser] = useState(null);
  // ...
};
```
````

## Anti-patterns

- Kitchen sink approach (including everything instead of what matters most)
- Duplicating README or other docs instead of linking to them
- Adding obvious instructions already enforced by linters/formatters
- Duplicating the same rules in both copilot-instructions.md and AGENTS.md
- Using settings-based code generation or test generation instructions (deprecated in VS Code 1.102 — use instruction files instead)

## Validation Checklist

- Stored at `.github/copilot-instructions.md` (workspace root)
- No YAML frontmatter
- Rules are specific and testable
- If AGENTS.md also exists, ensure no duplicate rules between the two files
- If Claude Code is also used in the workspace, ensure CLAUDE.md and copilot-instructions.md complement rather than duplicate each other
