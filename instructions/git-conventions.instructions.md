---
name: Git Commit Conventions
description: Commit message format, validation, and automatic delivery for every repository.
applyTo: "**"
---

# Git Commit Conventions

All commits follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## Format

```text
<type>: <subject>

<body>

<footer>
```

- **type**: `feat` | `fix` | `docs` | `style` | `refactor` | `test` |
  `chore` | `ci`
- **subject**: ≤50 chars, imperative mood, lowercase, no period
- **body** (optional): wrap at 72 chars, explain what and why
- **footer** (optional): `Closes #N`, `Related-To: TICKET-N`

## Pre-commit Validation

When committing `.md` files, run markdown linting first:

```bash
npx markdownlint-cli2
```

## Repository-local Git Hooks

If a repo contains `.githooks/`, activate with:

```bash
git config core.hooksPath .githooks
```

One-time per clone. Sets repo-local config to use checked-in hooks.

## Delivery workflow

- Apply this workflow to every task in every Git repository. After each coherent,
  validated work item, MUST commit the task changes, push the branch, and merge
  into the repository's default or designated integration branch.
- Treat implementation, fixes, and documentation requests as authorization for
  this delivery workflow. Do not stop at uncommitted changes, a local commit,
  or an open pull request when the required checks and merge permissions permit
  completion. Do not request routine commit, push, or merge confirmation.
- MUST follow the repository's pull-request workflow, run its required checks,
  fix task-related failures, and wait for required checks and reviews before
  merging. MUST NOT bypass branch protection, review requirements, or checks.
- Stage only task changes. Preserve unrelated work, the human Git author,
  legitimate trailers, and the configured assistant attribution.
- If a remote is absent, access is denied, or an external review is required,
  report the exact blocker, completed steps, and pending action. MUST NOT invent
  a publication destination or claim an incomplete push or merge succeeded.
- Explicit task-specific limits, including read-only work or instructions not
  to commit, push, or merge, take precedence over this default. "All changes"
  means authorized task changes, not unrelated changes from other writers.
