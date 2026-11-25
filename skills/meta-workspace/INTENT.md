# Intent

Make `<projects-root>/_meta/` the primary home for generated documents, reports, notes, and similar transient content, in a predictable, dated structure outside any single project.

## Goals

1. The meta workspace is used as the primary home for generated documents, reports, notes, and similar types of content, unless there is another clearly more appropriate destination.
2. Content is placed in a specified directory structure, with clear rules for when to use each directory.
3. All added content is consistently dated and labeled.
4. The purpose and intent of the directory and its contents are clear: these files are generally transient in nature and lose relevance quickly over time.

## Requirements

- Use the `<projects-root>/_meta/` directory for notes, documents, scripts, and other generally transient content spanning across projects.
- Directory structure: `files/`, `notes/`, `reports/`, `scratch/`, `scripts/`, `specs/`. Extensible if additional patterns arise, but agents should prefer conformance absent a clear justification.
- Content uses the current ISO-8601 date as a prefix, such as `2026-11-25-<label>`. Labels are concise but meaningful.
- Encourage subdirectories under the top-level directories where useful. They follow the same dating and labeling conventions.
- Not a hidden dot-directory; not scattered at the projects root.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-14: The operator confirmed the skill is still in use and must be kept.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 121 to about 40 lines; examples condensed into a table, MUST/MAY lists replaced with rules.
- 2026-11-25: Operator redefined the skill: `_meta/` becomes the primary home for generated content (not only cross-project work), with folders `files/`, `notes/`, `reports/`, `scratch/`, `scripts/`, `specs/`, `YYYY-MM-DD-<label>` names on all content including subdirectories, and an explicit transient purpose. Goals and requirements rewritten from that request.
- 2026-11-25: [agent] Placement order: a user-named location, then a clearly better home (content that ships with a project), then `_meta/`. Dates are creation dates and survive edits; same-subject items are updated rather than duplicated. `_meta/README.md` is the only undated file and lists any added top-level folder. Replaced the lowercase-kebab-only naming and the one-level nesting limit.
- 2026-11-25: [agent] Codex review (gpt-6.2-astra) fixes: the projects root comes from the main checkout, never a worktree folder; tool-required file names (such as `pyproject.toml`) are kept inside dated folders; an existing `_meta/README.md` gains rows for missing standard folders.
