# Intent

Keep `.gitignore` files consistent and easy to update across projects, by separating shared templates from project-specific rules.

## Goals

1. Every `.gitignore` has the same three-part structure.
2. Upstream templates can be refreshed by replacing their sections wholesale, because they are never edited.
3. Project-specific intent is visible in one place.

## Requirements

- Apply to every `.gitignore` task: create, update, review, and refactor.
- Exactly three section groups in this order: base template reference, one or more unaltered GitHub gitignore templates, one project-specific rules section.
- The base section copies the canonical base template unaltered.
- Each GitHub template section starts with exactly one `### <Name> Template` heading, and its text stays unaltered.
- Exactly one `### Project-Specific Rules` section, holding all additions and overrides, including re-adding patterns ignored by earlier templates.
- Exactly one blank line between sections. No extra section types.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. Moved the base template from `references/` to `assets/base.gitignore`, because it is a file to copy, not reading. Replaced MUST rules with plain imperatives, and added fetching the current upstream text and a `git status --ignored` check.
