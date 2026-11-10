---
name: meta-workspace
description: "Use when creating planning documents, notes, reports, specs, or scripts that serve a supervisory, cross-project, or orchestration role — not tied to a single project codebase. Directs all such work to the _meta/ directory in the projects root."
---

# Meta-Workspace Skill

## Overview

A "projects root" directory (e.g., `~/Projects`) typically contains many individual project subdirectories. Work that *spans* those projects or *orchestrates* them — planning, notes, specs, reports, scripts — does not belong inside any single project. It belongs in `_meta/`, a dedicated orchestration directory that lives at the projects root.

The underscore prefix causes `_meta/` to sort prominently at the top of directory listings on Windows, macOS, and Linux without being hidden. The name is unambiguous and portable: apply the same `_meta/` convention in any analogous projects-root directory.

## Directory Structure

```
<projects-root>/
└── _meta/
    ├── README.md      # Describes the purpose and structure of _meta/
    ├── notes/         # Running notes, ideas, observations across projects
    ├── reports/       # Generated or written summaries and status reports
    ├── scripts/       # Orchestration and utility scripts that span projects
    └── specs/         # Specifications and design documents for planned work
```

Create additional subdirectories when work does not fit the standard set. Name them in lowercase-kebab-case.

## When to Use `_meta/`

Place work in `_meta/` when it meets **any** of these conditions:

- It concerns multiple projects simultaneously (e.g., a migration plan, a cross-project audit)
- It is supervisory in nature — tracking, planning, or reporting on projects rather than implementing within them
- It is a script or tool used to manage or automate project-level tasks (not a deliverable within a project)
- It is a spec or design document for work that has not yet been started in a specific project

Do **not** place this work in an individual project directory, a hidden dot-directory (e.g., `.docs/`), or scattered at the projects root.

## Procedure

### Creating a New Orchestration Document or Script

1. Identify the projects root (the directory containing individual project subdirectories).
2. Confirm `_meta/` exists at that root. If it does not, create it with the standard subdirectory structure above and a `README.md`.
3. Select the correct subdirectory:
   - Planning, ideas, observations → `notes/`
   - Requirements, designs, API contracts for future work → `specs/`
   - Status updates, summaries, audits → `reports/`
   - Automation, utilities, orchestration code → `scripts/`
4. Use lowercase-kebab-case filenames (e.g., `q2-migration-plan.md`, `audit-report-2026.md`).
5. If a standard subdirectory does not fit, create a new one with a lowercase-kebab-case name.

### Initializing `_meta/` From Scratch

When `_meta/` does not yet exist in the projects root:

1. Create `_meta/` and its four standard subdirectories (`notes/`, `specs/`, `reports/`, `scripts/`).
2. Create `_meta/README.md` with:
   - A single `# _meta` heading
   - A brief explanation of the directory's purpose
   - A table listing each subdirectory and its purpose
3. Proceed to place the triggering work in the appropriate subdirectory.

## Constraints

**MUST:**

- Place all supervisory, cross-project, and orchestration work in `_meta/` at the projects root.
- Use the four standard subdirectories (`notes/`, `specs/`, `reports/`, `scripts/`) before creating new ones.
- Name all files and subdirectories in lowercase-kebab-case.
- Create `_meta/README.md` if it does not exist when initializing the directory.

**MUST NOT:**

- Place orchestration work inside an individual project's repository.
- Use a hidden dot-directory (e.g., `.docs/`, `.meta/`) for this purpose — hidden directories are easily overlooked and misidentified.
- Scatter planning or reporting files at the projects root without placing them in `_meta/`.
- Use spaces, mixed case, or snake_case in `_meta/` filenames.

**MAY:**

- Create additional subdirectories within `_meta/` beyond the standard four when a project warrants it (e.g., `_meta/templates/`, `_meta/archives/`).
- Nest subdirectories one level deep within the standard subdirectories (e.g., `_meta/specs/cli-tools/`).

## Examples

### Example 1: Writing a spec for a new project

**Scenario:** The user asks for a specification document for a new CLI tool that does not yet have a project directory.

**Correct action:** Create `<projects-root>/_meta/specs/cli-tool-name.md`.

**Incorrect action:** Creating a new project directory and placing the spec inside it before the project exists, or placing the spec at the projects root.

---

### Example 2: Planning a migration across several projects

**Scenario:** The user asks for a migration plan that affects three existing projects.

**Correct action:** Create `<projects-root>/_meta/notes/migration-plan.md` (or `reports/` if it is a formal report).

**Incorrect action:** Placing `migration-plan.md` inside one of the three project directories.

---

### Example 3: An automation script that operates on multiple projects

**Scenario:** The user asks for a PowerShell script that clones and updates all projects in the projects root.

**Correct action:** Create `<projects-root>/_meta/scripts/update-all-projects.ps1`.

**Incorrect action:** Adding the script to an individual project's repository or to the projects root directly.

---

### Example 4: `_meta/` does not yet exist

**Scenario:** The user asks to create a new planning note and `_meta/` is absent.

**Correct action:** Create `_meta/` with all standard subdirectories, create `_meta/README.md`, then create `_meta/notes/<note-name>.md`.
