# Intent

Make agents write documentation that readers can scan and act on, and organize project documentation so knowledge is discoverable, its authority explicit, and its upkeep affordable. Merges `technical-writing` and `project-documentation`.

## Goals

1. Readers find the key result, action, or constraint first.
2. Procedures are executable: prerequisites, warnings, exact values, checkpoints, and recovery.
3. Every fact has one canonical source, and its trust level is honest.
4. Documentation structure is predictable across projects, while explicit profiles can extend it.

## Requirements

- Wording rules apply in any format or location, not only in docs folders.
- Apply selected ASD-STE100 principles without claiming compliance.
- Prefer numbered steps, bullets, tables, and diagrams over long prose paragraphs.
- Root `README.md` is the entrance; deeper knowledge lives in `docs/`; every docs directory has a content-bearing `README.md` that indexes its children.
- Reserved directory meanings: `decisions/`, `architecture/`, `guides/`, `reference/`, `operations/`, `plans/`.
- Lifecycle metadata in YAML frontmatter, validated by a JSON Schema, with no timestamp fields.
- Never fabricate a reviewer or mark content verified because a model wrote it.
- Profiles (personal, repository, team, enterprise) extend the conventions explicitly; unresolved conflicts are surfaced, not silently resolved.
- Do not adopt a whole external framework (such as OKF) or a private organizational taxonomy.

## Log

- 2026-11-10: Imported into the SkillSinc library layout as `technical-writing` and `project-documentation`. Requirements above are taken from those skills.
- 2026-11-22: [agent] Merged both into `technical-documentation` during the migration to the `skill-development` standard. Each skill's description pointed at the other, they split one job (writing docs) by an unclear line, and "writing" is a gerund. Moved the JSON Schema to `assets/`, profile rules to `references/structure.md`, and STE sources to `references/writing.md`.
