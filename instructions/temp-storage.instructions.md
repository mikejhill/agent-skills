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

**Naming**: `.tmp/{dir}/{session-id}-{description}.{ext}`
where session-id is 8 random alphanumeric chars.

Alternatives: timestamp (`YYYYMMDD-HHMMSS-desc.ext`), stage-based
(`01-step.ext`), or plain (`desc.ext`) for cross-session files.

## Rules

- Create files liberally. Preserve for debugging and rollback.
- Never commit `.tmp/`. Must be in `.gitignore`.
- Do not delete files unless necessary for state accuracy.
- Avoid disrupting files in use by other agents.
