# Intent

Execute agent work in isolated git worktrees so that parallel tasks, subagent operations, and background work never modify the operator's working tree.

## Goals

1. The operator's working tree, staging area, and uncommitted changes are never touched by isolated work.
2. Every worktree follows a deterministic lifecycle from creation through merge or discard, with no orphans.
3. Parallel agents produce independent, reviewable changesets.

## Requirements

- Cover parallel multi-agent work, subagent tasks that must not disrupt the operator's workspace, and one-off isolated operations.
- Worktrees in a persistent, user-invisible location not subject to OS temp cleanup: `~/.local/share/agent-worktrees/` (or `XDG_DATA_HOME`), path `<repo-name>--<branch-suffix>`.
- Branches `worktree/<purpose>-<unique>` with a mandatory random suffix; always a new branch from `HEAD`.
- Five phases: create, execute, commit, apply, clean up.
- Apply strategy chosen by decision criteria (PR, push and share, sequential merge, direct merge, share only). Conflicts are reported to the operator, never auto-resolved.
- Never delete a pushed branch with an open PR, or unmerged work the operator has not discarded.
- Out of scope: git internals, non-git VCS, container or VM isolation, CI design.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 353 to about 70 lines; commands and the parallel pattern moved to `references/`. The base path is kept, although the standard's table has no slot for persistent data, because worktrees hold uncommitted work that is neither temp nor rebuildable cache, and moving it would orphan existing worktrees. Fixed the suffix recipe (the old Bash one produced 8 non-random characters and needed `xxd`), and made subagent dispatch wording harness-neutral.
