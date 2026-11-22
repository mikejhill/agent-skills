---
name: meta-workspace
description: >-
  Puts cross-project and supervisory work (plans, notes, specs, reports,
  scripts that span projects) in a _meta/ folder at the projects root. Use when
  creating a document or script that is not tied to a single project's
  codebase.
---

# Meta workspace

Work that spans or orchestrates projects lives in `_meta/` at the projects root (the folder that holds the individual project folders, such as `~/Projects`). The underscore sorts it first in listings on every OS without hiding it.

```text
<projects-root>/_meta/
├── README.md   # purpose and a table of subfolders
├── notes/      # plans, ideas, observations across projects
├── specs/      # designs and requirements for work not yet in a project
├── reports/    # status reports, summaries, audits
└── scripts/    # automation that operates across projects
```

## When it applies

Use `_meta/` when the work concerns several projects, tracks or reports on projects rather than implementing inside one, automates project-level tasks, or specifies work that has no project folder yet.

## Rules

- Never put this work inside one project's repository, at the projects root itself, or in a hidden folder such as `.meta/` or `.docs/`.
- If `_meta/` is missing, create it with the four subfolders and a `README.md` (a `# _meta` heading, one line of purpose, and a table of subfolders), then add the file.
- Use the standard subfolders first. Add another lowercase-kebab-case subfolder (such as `templates/`) only when nothing fits. Nest at most one level inside a standard subfolder.
- Name files in lowercase-kebab-case: `q2-migration-plan.md`, `update-all-projects.ps1`.

## Examples

| Request | Location |
| --- | --- |
| Spec for a CLI tool that has no project yet | `_meta/specs/cli-tool-name.md` |
| Migration plan affecting three projects | `_meta/notes/migration-plan.md` |
| Script that pulls every project | `_meta/scripts/update-all-projects.ps1` |
