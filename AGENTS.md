# Agent Instructions

This repository is a feature library for other workspaces, not a project workspace. Items here are not active in this repository; SkillSinc distributes them.

## Placement

| Feature type       | Location                   | File pattern                      |
| ------------------ | -------------------------- | --------------------------------- |
| Skills             | `skills/<name>/`           | `SKILL.md` (required)             |
| Instructions       | `instructions/`            | `<name>.instructions.md`          |
| Agents             | `agents/`                  | `<name>.agent.md`                 |
| Prompts            | `prompts/`                 | `<name>.prompt.md`                |
| Resources          | `resources/`               | `<name>.md`                       |
| Intent files       | Alongside the feature      | `INTENT.md`                       |

## Rules

- Names are lowercase and hyphen-separated.
- Content must be public-safe: no credentials, private hostnames, personal account data, or machine-specific absolute paths. Personal or private items belong in the separate private library.
- Run `npx markdownlint-cli2` before committing Markdown.
- After changes, run `skillsinc plan` and review the result before `skillsinc sync`.
