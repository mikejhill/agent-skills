---
name: agent-tmp-directory
description: Temporary file management in `.tmp/` for agent artifacts, session state, and intermediate results.
applyTo: "**"
---

# Agent Temporary Directory

Store all ephemeral files in `.tmp/`. Use liberally for state
preservation, rollback, debugging, and inter-agent coordination.

## Path Conventions

```text
.tmp/
  checkpoints/   # State before risky operations
  scripts/       # Generated scripts
  outputs/       # Tool call outputs
  reports/       # Analyses and reports
  info/          # Inferred/cached information
```

Skills write to `.tmp/<skill-name>/` instead.

**Naming**: `{kind}-{YYYYMMDD-HHMMSS}-{description}.{ext}` in local time,
for example `report-20261122-175433-auth-flow.md`. Never overwrite; on a
clash append `-2`, `-3`, and so on. Use plain names (`desc.ext`) only for
files meant to persist across sessions.

## Rules

- Create files liberally. Preserve for debugging and rollback.
- Never commit `.tmp/`. Must be in `.gitignore`.
- Do not delete files unless necessary for state accuracy.
- Avoid disrupting files in use by other agents.
