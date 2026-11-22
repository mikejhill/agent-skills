# Parallel and concurrent patterns

## Orchestrating parallel agents

1. **Plan:** split the task into independent subtasks, and give each agent a unique name.
2. **Create** one worktree and branch per agent.
3. **Dispatch** all agents at once. Each prompt states its worktree path, branch name, and the main-tree boundary.
4. **Wait** for every agent to finish.
5. **Verify** each branch has a commit with the expected changes (`git log <branch> -n 3`).
6. **Merge** by the apply table in `SKILL.md`, one branch at a time when they may overlap.
7. **Clean up** all worktrees, and delete merged branches.

```text
worktree/agent-alpha-a3f1b2  -> <base>/my-project--agent-alpha-a3f1b2/
worktree/agent-beta-7c9e01   -> <base>/my-project--agent-beta-7c9e01/
worktree/agent-gamma-d8e4c1  -> <base>/my-project--agent-gamma-d8e4c1/

merge alpha -> clean
merge beta  -> conflict: report files and branches, wait for the user
merge gamma -> clean
remove 3 worktrees, delete 3 merged branches
```

## Working while the user edits

1. Create a worktree for the agent task and dispatch the agent there.
2. The user keeps editing the main tree freely.
3. When the agent finishes, report the branch name.
4. The user decides when and how to integrate: merge, cherry-pick, or discard.

This suits long tasks such as test generation, documentation updates, or exploratory refactors.
