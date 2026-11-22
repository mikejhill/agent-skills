---
name: worktree-isolation
description: >-
  Run agent work in isolated git worktrees, so parallel agents, subagents, or
  background tasks never touch the user's working tree: placement, branch
  naming, commit, merge or PR, and cleanup. Use when work needs filesystem
  isolation from the current checkout.
---

# Worktree isolation

Give each isolated task its own git worktree and branch, with a fixed lifecycle: create, execute, commit, apply, clean up.

## When to use

Use it when parallel agents may touch overlapping files, when a subagent must not disturb the user's staged or uncommitted changes, when the user keeps editing while an agent works, or when changes are speculative and should be easy to discard. Skip it for a single-file change with no conflict risk, when the user asks for in-place changes, or outside a git repository.

## Placement and naming

- Base directory: `${XDG_DATA_HOME:-~/.local/share}/agent-worktrees/` on every OS (Windows: `%USERPROFILE%\.local\share\agent-worktrees\`). It persists and is not subject to temp cleanup. Never create worktrees beside or inside the repository.
- Worktree path: `<base>/<repo-name>--<branch-suffix>/`, where `<repo-name>` is the basename of the repository root.
- Branch: `worktree/<purpose>-<6 hex chars>`, such as `worktree/agent-alpha-a3f1b2` or `worktree/refactor-auth-d8e4c1`. The random suffix is mandatory, because leftover branches from earlier runs collide. Keep names under 100 characters.
- Always create a new branch from the current `HEAD`. Never check out an existing branch into a worktree.

Commands for Bash and PowerShell are in [commands.md](references/commands.md).

## Lifecycle

1. **Create** the worktree and confirm it with `git worktree list`.
2. **Execute** with the agent's working directory set to the worktree. Every file operation and command uses the worktree path, never the main tree. When dispatching a subagent, tell it the worktree path, the branch name, and that it must not read or write under the main repository path.
3. **Commit** all changes on the worktree branch, following the repository's commit conventions. Parallel agents put their identity in the scope: `feat(alpha): ...`. A subagent commits its own work before reporting; the orchestrator checks the commit exists.
4. **Apply** with the first matching strategy in the table below.
5. **Clean up**: `git worktree remove <path>`, then `git worktree prune`. Delete the branch only if it is merged or the user discarded it (`git branch -d`, or `-D` for discarded work). Never delete a branch with an open PR or unmerged, undiscarded changes. Remove the worktree directory even when keeping the branch.

| Condition | Strategy |
| --- | --- |
| Speculative or experimental | Report the branch name only. Never push or merge |
| The user asked for a PR | Push the branch and open a PR |
| Changes need human review first | Push and report the branch name |
| Several branches touch overlapping files | Merge one at a time; stop on conflict and report the files and branches |
| Independent, low-risk changes | `git merge --no-ff <branch>` from the main tree |

Never auto-resolve merge conflicts; the user decides. After a merge, check `git status --short`. Run any further verification in a new worktree, not the main tree.

| Context | Cleans up |
| --- | --- |
| Orchestrated subagents or parallel agents | The orchestrator, after all merges |
| Single agent with no orchestrator | That agent |
| Branch pushed or shared for review | The user |

## References

- [commands.md](references/commands.md): read when creating or removing worktrees. Bash and PowerShell commands.
- [parallel.md](references/parallel.md): read when orchestrating several agents in parallel, or running an agent while the user keeps working.
