---
name: meta-workspace
description: >-
  Puts generated documents, reports, notes, specs, scripts, and other transient
  files in a dated, structured _meta/ folder at the projects root. Use when
  creating any of these that does not belong in a project's own files or a
  location the user named.
---

# Meta workspace

`<projects-root>/_meta/` is the default home for content an agent generates that is not part of a project's own files: documents, reports, notes, specs, scripts, and supporting files. The projects root is the folder that holds the individual project folders, such as `~/Projects`. The underscore sorts it first without hiding it.

Treat everything here as transient working material. It is dated so the user can see at a glance how stale it is, and it loses relevance quickly. Nothing here is a source of truth: anything that must last moves into the project it concerns.

## Where content goes

1. A location the user named.
2. A clearly more appropriate home, such as a project's own docs, code, or tests when the content ships with that project.
3. Otherwise `_meta/`, even when the content concerns only one project.

If the projects root is unclear, use the parent folder of the current project when it holds other projects; otherwise ask once. If it is not reachable from this session, put the file where the session can deliver it and tell the user.

## Structure

```text
<projects-root>/_meta/
├── README.md   # purpose of _meta/ and a table of its folders
├── files/      # supporting material: downloads, exports, data, images, attachments
├── notes/      # informal working notes: plans, ideas, findings, research, meeting notes
├── reports/    # finished output for reading: status reports, reviews, audits, analyses, comparisons
├── scratch/    # disposable experiments and intermediate output, safe to delete at any time
├── scripts/    # runnable automation and one-off scripts, often across projects
└── specs/      # designs, requirements, and proposals for work not yet in a project
```

- Pick the folder by what the content is, not which project it concerns. A finished write-up is a report; working thoughts toward it are notes; a script that produced it is a script; its raw data is files.
- If `_meta/` or a folder is missing, create it. Create `README.md` with the table above if it is missing.
- Conform to these folders. Add another top-level folder only when content recurs that clearly fits none of them, and add it to the `README.md` table with a one-line purpose.

## Naming

Every file and folder you add under the top-level folders is named `YYYY-MM-DD-<label>`, using today's local date (ISO 8601).

- Label: two to five lowercase-kebab-case words that say what it is about: `2026-11-25-uv-migration-plan.md`, `2026-11-25-pull-all-projects.ps1`.
- The date is the creation date. Keep it when you later edit the item.
- Before creating, check for an item on the same subject. Update it if it is the same piece of work; otherwise choose a more specific label.
- Only `_meta/README.md` and the top-level folders themselves are undated.

## Subfolders

Use a subfolder inside a top-level folder when a piece of work has several files, such as a report with its data and charts, or a spec with diagrams. Name the subfolder and every file in it with the same convention, and keep nesting shallow.

```text
reports/2026-11-25-dependency-audit/
├── 2026-11-25-dependency-audit.md
└── 2026-11-25-outdated-packages.csv
```

## Examples

| Request | Location |
| --- | --- |
| Summarize open PRs across my repos | `_meta/reports/2026-11-25-open-pr-summary.md` |
| Plan migrating all projects to uv | `_meta/notes/2026-11-25-uv-migration-plan.md` |
| Spec a CLI tool that has no project yet | `_meta/specs/2026-11-25-backup-cli/` with its files |
| Script that pulls every project | `_meta/scripts/2026-11-25-pull-all-projects.ps1` |
| Try a library API before using it | `_meta/scratch/2026-11-25-httpx-retry-test/` |
| Add a section to a project's README | The project's README, not `_meta/` |
