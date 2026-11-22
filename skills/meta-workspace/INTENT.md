# Intent

Give supervisory, cross-project, and orchestration work one predictable home that is not inside any single project.

## Goals

1. Cross-project work never lands inside an individual project's repository.
2. The location is easy to find and the same in every projects root.

## Requirements

- Directs all planning documents, notes, reports, specs, and scripts that serve a supervisory, cross-project, or orchestration role to `_meta/` in the projects root.
- Standard subdirectories: `notes/`, `specs/`, `reports/`, `scripts/`, plus `_meta/README.md`.
- Not a hidden dot-directory; not scattered at the projects root.
- Lowercase-kebab-case names for files and subdirectories. Extra subdirectories only when the standard ones do not fit; nest at most one level.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-14: The operator confirmed the skill is still in use and must be kept.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 121 to about 40 lines; examples condensed into a table, MUST/MAY lists replaced with rules.
