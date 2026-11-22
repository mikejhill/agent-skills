---
name: project-backlog
description: >-
  Manage a project's idea backlog and specs under specs/: capture ideas,
  promote them to spec directories with spec.md, iterate on specs, and archive
  finished ones. Use when the user adds to, reviews, or promotes backlog items,
  or works on or archives a spec.
---

# Project backlog

Run a three-stage lifecycle under `specs/` at the project root: backlog, specification, archive.

```text
specs/
├── project-backlog.md      # stage 1: compact idea list
├── <item-slug>/            # stage 2: one directory per spec
│   ├── spec.md             #   required
│   └── <topic>.md          #   optional supporting files
└── archive/<item-slug>/    # stage 3: finished specs, moved here
```

## Backlog

`project-backlog.md` holds a title, a one-line purpose, `## Category` headings, and `### Item Title` entries with a few sentences each. It is a list of ideas, not a task tracker: no status, priority, owner, or dates.

- **Add:** append under the best-fitting category (create one if none fits), confirm in one line, and return to what the user was doing. Quick capture must not derail the conversation.
- **List, modify, remove:** find items by title. If titles collide across categories, ask which one, showing category and title. Remove a category heading when its last item goes.
- When an item grows past a short paragraph, suggest promoting it.

## Specs

- **Promote:** derive a kebab-case slug from the title. If `specs/<slug>/` exists, ask whether to merge or pick another slug. Create `specs/<slug>/spec.md` following [spec-structure.md](references/spec-structure.md), expanding the backlog entry. Then remove the item from the backlog and present the spec for review.
- **Iterate:** read the whole spec directory first. Put large supporting material (research, sub-designs, diagrams) in kebab-case files beside `spec.md`, and link them from it. One level of subdirectories at most.
- **List:** directories under `specs/` except `archive/`, with the first heading of each `spec.md`.
- **Execute:** read `spec.md` and its supporting files and use them to guide implementation. This skill prepares specs; it does not implement them.

## Archive

- Archive only once the spec is executed or dropped. Move (not copy) `specs/<slug>/` to `specs/archive/<slug>/`. On a name clash, ask the user.
- Optionally add a one-line archival note at the top of `spec.md` saying why.
- Never delete archived specs.

## References

- [spec-structure.md](references/spec-structure.md): read when creating or restructuring a `spec.md`.
- [example-spec.md](references/example-spec.md): read for a complete filled-in spec.
