# Intent

Tell agents where temporary files, clones, and scratch work go, how to name them, and
when to remove them, so nothing they create outlives its task on the user's machines.

## Goals

1. Workspace scratch lives in `.tmp/`, is gitignored, and is kept for debugging.
2. Disposable working directories outside a workspace (review clones, verification
   and repro directories) live under one scratch root:
   `<system-temp>/agent-skills/scratch/` (Unix: `agent-skills-<uid>/scratch/`). They
   never go in the user's project folders, home folder, or loose in the temp folder.
3. Each one is dated (`<kind>-<YYYYMMDD-HHMMSS>-<slug>`) and removed when its task
   ends, unless it holds work or results with no other copy.
4. A sweep removes stale entries (more than 7 days old by name) so leftovers from
   crashed or forgetful sessions don't accumulate. It never deletes a `KEEP` entry or a
   Git checkout with unsaved work, and never follows links out of the root.
5. Worktrees, caches, and persistent state keep their own locations and rules.

## Requirements

- When a session delegates work to another session or machine, the brief names the
  scratch path and the last brief asks for removal on the machine that holds it.
- Locked or foreign-owned leftovers are reported, never deleted with escalated rights.
- Harness-neutral wording; harness-specific troubleshooting belongs to the relevant
  skill.

## Log

- 2026-11-22: [operator] "Some agent executions leave stale clones around, such as the
  agent-skills-review-20261122 directory. Figure out what causes these and devise a
  solution."
- 2026-11-22: [agent] Root cause: review briefs sent to the user's machines cloned into
  a projects `temp` folder and said to leave the clone in place, with no removal step.
  Verification folders went loose into `%TEMP%`. The old rule covered only `.tmp/` and
  said not to delete files. Added the scratch root, dated names, removal at task end,
  the delegation rule, the `KEEP` marker, and a sweep (PR #25).
- 2026-11-22: [agent] Codex reviews hardened the sweep over three rounds: it selects
  by the full name timestamp; validates the temp base, parent, and root (no links,
  owner-only, Windows path inside the profile); fails instead of warning so callers
  stop; and keeps checkouts with uncommitted or untracked files (regardless of
  `status.showUntrackedFiles`), stashes, commits on no remote, nested checkouts, or a
  failing check. PR heads are fetched into remote-tracking refs so clean review clones
  don't look unpushed.
- 2026-11-22: [agent] Codex round 4 (final): a failed folder scan or a missing Git
  now keeps the entry or stops the sweep; the Unix base is resolved to its physical
  path (macOS `/tmp` is a link) and every ancestor must be trusted. Stopped after four
  rounds, as with PRs #23 and #24, since later rounds found edge cases in the previous
  round's fixes.
