# Intent

Give a project a lightweight lifecycle for ideas: capture them cheaply, design them in dedicated specs when ready, and archive them once executed.

## Goals

1. Capturing an idea costs one edit and one line of reply, without disrupting current work.
2. Specs are consistent and complete enough to execute from.
3. Finished work leaves the active view but is never lost.

## Requirements

- Three stages under `specs/` at the project root: backlog (`specs/project-backlog.md`), specification (`specs/<slug>/spec.md`), archive (`specs/archive/<slug>/`).
- Backlog items are compact, grouped by category, with no status fields, priority numbers, or other project-management metadata.
- Every spec gets its own kebab-case directory with a primary `spec.md`, even if it is a single file. Specs follow the canonical structure in `references/spec-structure.md`.
- Promoted items are removed from the backlog.
- Completed specs are moved, not copied, to the archive. The archive is append-only.
- The skill prepares specs for execution; it does not implement them.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 312 to about 50 lines: per-operation procedures condensed to one line each, examples and MUST/MAY lists removed.
