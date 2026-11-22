# Intent

Produce correct, readable Mermaid diagrams that render identically on GitHub, GitLab, and local tooling, and export them to images when needed.

## Goals

1. Diagrams render on the target platform the first time, with no silent failures.
2. Each diagram is focused on one concept and readable at a glance.
3. Export to images works with one command.

## Requirements

- Cover all Mermaid diagram types, type selection, syntax rules, pitfalls, GitHub compatibility, and embedding in Markdown.
- Bundled CLI script for PNG, SVG, and PDF export, wrapping `@mermaid-js/mermaid-cli`.
- Under 15 nodes per diagram; descriptive labels; ASCII-only syntax; quoted special characters; a text description near each diagram.
- No `%%{init:}%%` theme directives for GitHub-hosted documentation; nested subgraphs at most two levels.
- Out of scope: Mermaid internals and plugins, other diagram tools, static site generator integration.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 227 to about 55 lines; syntax basics moved to `references/syntax.md`, and pitfalls and constraints merged into one rule list. The export script's temp files now use the dated `diagram-<YYYYMMDD-HHMMSS>-<id>` name, and `--help` no longer prints the comment opener.
