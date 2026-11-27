# Agent Instructions

This repository is a feature library for other workspaces, not a project workspace. Items here are not active in this repository; SkillSinc distributes them.

## Placement

| Feature type       | Location                   | File pattern                      |
| ------------------ | -------------------------- | --------------------------------- |
| Skills             | `skills/<name>/`           | `SKILL.md`, `README.md`, `INTENT.md` (see `agent-context`) |
| Instructions       | `instructions/`            | `<name>.instructions.md`          |
| Agents             | `agents/`                  | `<name>.agent.md`                 |
| Prompts            | `prompts/`                 | `<name>.prompt.md`                |
| One-harness items  | `harnesses/<harness>/<kind>/` | Same as the root kind folder   |
| Intent files       | Alongside the feature      | `INTENT.md` or `<name>.intent.md` (see `agent-context`) |

## Rules

- Names are lowercase and hyphen-separated.
- Content is harness-neutral: no tool names, invocation syntax (`#tool:`, `#file:`), or paths specific to one harness. Use the portable Agent Skills format.
- An item that only works in or applies to one harness goes under `harnesses/<harness>/` (`<harness>` is a SkillSinc profile: `claude`, `codex`, `copilot`, `vscode`), never at the root with a routing exclude. Use only kinds that profile writes. Its description or intent file says which harness it is for. See the README's Harness-specific items section (shared discovery paths, migration).
- Content must be public-safe: no credentials, private hostnames, personal account data, or machine-specific absolute paths. Personal or private items belong in the separate private library.
- Run the checks in the README's Checks section before committing. CI runs the same checks, and `main` requires `ci-pass` and `pr-title`.
- Merge a pull request only after `ci-pass` and `pr-title` are green on its latest commit. Prefer auto-merge. The owner's ruleset bypass is for the owner to use explicitly; agents never use it.
- After changes, run `skillsinc plan` and review the result before `skillsinc sync`.
