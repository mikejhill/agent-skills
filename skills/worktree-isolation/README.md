# worktree-isolation

Runs agent work in separate git worktrees, each on its own branch, so parallel agents, subagents, and background tasks never change the files you are working on.

## Use

Loads automatically when work needs isolation from your checkout. Examples:

- "Have three agents each try a different fix in parallel."
- "Generate tests in the background while I keep editing."

## Results

- Worktrees live in `~/.local/share/agent-worktrees/<repo>--<branch-suffix>/` (or under `XDG_DATA_HOME`), on branches named `worktree/<purpose>-<hex>`.
- Work is merged, pushed as a PR, or left on its branch for you, depending on the task. Merge conflicts are always left for you to resolve.
- Worktrees are removed afterwards. Branches are deleted only when merged or discarded by you.

## Requirements

- Git 2.20 or later.
