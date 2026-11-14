---
name: worktree-isolation
description: "Use when executing tasks that require filesystem isolation from the current working tree. Covers parallel multi-agent work, subagent tasks that must not disrupt the operator's workspace, and one-off isolated operations. Provides git worktree lifecycle management including creation, branch naming, agent execution, commit strategy, merge/PR workflow, and cleanup."
---

# Worktree Isolation

## Objective

Execute agent work in isolated git worktrees so that parallel tasks, subagent operations, and background work never modify the operator's working tree. Each worktree gets its own branch, its own filesystem snapshot, and a deterministic lifecycle from creation through merge or discard.

## Scope

**In-scope:**

- Creating and configuring git worktrees for agent use
- Branch naming and worktree directory placement
- Running agents (main or sub) inside a worktree
- Committing, merging, pushing, and creating PRs from worktree branches
- Worktree cleanup and orphan prevention
- Parallel execution patterns for multi-agent workflows
- Operator-concurrent workflows (agent works while human edits the main tree)

**Out-of-scope:**

- Git worktree internals or low-level plumbing commands
- Non-git version control systems
- Container-based or VM-based isolation
- CI/CD pipeline design

## When to Use This Skill

Activate this skill when any of the following apply:

- The harness is dispatching parallel subagents that may touch overlapping files
- A subagent needs to perform work without risk of corrupting the operator's staging area or uncommitted changes
- The operator wants to continue editing the working tree while an agent works in the background
- A task involves exploratory or speculative changes that should be easy to discard
- Multiple agents must each produce independent changesets for later review or merge

Do NOT use this skill when:

- The task modifies only a single file with no risk of conflict
- The operator explicitly requests in-place changes
- The repository is not a git repository

---

## Worktree Directory Placement

Place worktrees in a persistent, user-invisible location that is not subject to OS-level temporary-file cleanup. The base directory depends on the platform.

### Base Directory

All platforms use the same path under the user's home directory:

```text
~/.local/share/agent-worktrees/
```

If `XDG_DATA_HOME` is set, replace `~/.local/share` with its value.

Create the base directory on first use if it does not exist.

### Worktree Path Format

```text
<base-directory>/<repo-name>--<branch-suffix>/
```

**Example (Windows):**

```text
%USERPROFILE%\.local\share\agent-worktrees\my-project--agent-alpha\
```

**Example (Linux/macOS):**

```text
/home/user/.local/share/agent-worktrees/my-project--agent-alpha/
```

The `<repo-name>` component is the basename of the git repository root directory. The `<branch-suffix>` matches the final segment of the branch name (see below).

---

## Branch Naming

All worktree branches use a consistent prefix to distinguish them from human-created branches.

### Convention

```text
worktree/<purpose>-<unique>
```

**Rules:**

- `<purpose>` is a lowercase, hyphen-separated slug describing the task
- `<unique>` is a 6-character random hex suffix to prevent collisions (e.g., `a3f1b2`). Generate with: `$(git rev-parse --short=6 HEAD)$(date +%s | tail -c 3)` (Bash) or `(-join ((48..57)+(97..102) | Get-Random -Count 6 | ForEach-Object {[char]$_}))` (PowerShell)
- For parallel agents, incorporate the agent identity before the suffix: `worktree/agent-alpha-a3f1b2`
- For single-agent isolation, describe the task: `worktree/refactor-auth-d8e4c1`
- Maximum total branch name length: 100 characters
- The suffix is mandatory. Even sequential single-agent worktrees risk collision with leftover branches from previous runs.

**Examples:**

| Scenario                   | Branch name                            |
| -------------------------- | -------------------------------------- |
| Parallel agent "Alpha"        | `worktree/agent-alpha-a3f1b2`          |
| Parallel agent "Beta"         | `worktree/agent-beta-7c9e01`           |
| Isolated refactor task     | `worktree/refactor-auth-module-d8e4c1` |
| Background test generation | `worktree/generate-api-tests-f0b3a9`   |

---

## Lifecycle

Every worktree follows a five-phase lifecycle: **Create → Execute → Commit → Apply → Clean up**.

### Phase 1: Create

Create the worktree from the current HEAD of the active branch. Always create a new branch — never check out an existing branch into a worktree.

#### PowerShell (Windows)

```powershell
$RepoRoot   = git rev-parse --show-toplevel
$RepoName   = Split-Path $RepoRoot -Leaf
$BranchName = "worktree/agent-alpha-$(-join ((48..57)+(97..102) | Get-Random -Count 6 | ForEach-Object {[char]$_}))"
$Suffix     = ($BranchName -split '/')[-1]
$WtBase     = Join-Path $HOME ".local/share/agent-worktrees"
$WtPath     = Join-Path $WtBase "$RepoName--$Suffix"

if (-not (Test-Path $WtBase)) { New-Item -Path $WtBase -ItemType Directory -Force | Out-Null }

git worktree add $WtPath -b $BranchName
```

#### Bash (macOS/Linux)

```bash
repo_root=$(git rev-parse --show-toplevel)
repo_name=$(basename "$repo_root")
branch_name="worktree/agent-alpha-$(head -c3 /dev/urandom | xxd -p | cut -c1-6)"
suffix="${branch_name##*/}"
wt_base="${XDG_DATA_HOME:-$HOME/.local/share}/agent-worktrees"
wt_path="$wt_base/${repo_name}--${suffix}"

mkdir -p "$wt_base"

git worktree add "$wt_path" -b "$branch_name"
```

#### Verification

After creation, confirm the worktree exists:

```bash
git worktree list
```

Expected output includes a line for the new worktree with the correct branch.

### Phase 2: Execute

Run the agent (or subagent) with its working directory set to the worktree path. The agent operates exclusively within that directory.

**Rules for agents executing in a worktree:**

1. All file operations MUST use the worktree path, never the main repository path.
2. The agent MUST NOT `cd` to or modify files in the main working tree.
3. If the agent needs to run build/test commands, run them from the worktree directory.
4. The agent SHOULD treat the worktree as its entire world — it has full read/write access within it.

**Dispatching a subagent to a worktree:**

When dispatching a subagent via the task tool, include these instructions in the prompt:

- State the worktree path explicitly: "Your working directory is `<wt_path>`. All file operations use this path."
- State the boundary: "Do NOT read or write files under `<main_repo_path>`."
- Include the branch name so the agent can verify it is on the correct branch.

### Phase 3: Commit

After the agent completes its work, commit all changes on the worktree branch.

```bash
cd <wt_path>
git add -A
git commit -m "<conventional-commit-message>"
```

**Commit message rules:**

- Follow the repository's commit message conventions
- Include a clear description of what the agent accomplished
- For parallel agents, prefix the scope with the agent identity: `feat(alpha): add test.txt to all skills`

If the agent is a subagent, it SHOULD commit its own work before reporting completion. The orchestrator MUST verify the commit exists.

### Phase 4: Apply

After all worktree branches are committed, determine the appropriate strategy for integrating the work. Evaluate the criteria below in order — use the first matching strategy.

#### Decision Criteria

| Condition | Strategy | Action |
| --------- | -------- | ------ |
| Operator requested a PR | **Push + PR** | Push the branch to the remote and create a pull request |
| Changes need human review before integration | **Push + share** | Push the branch and report the branch name to the operator |
| Multiple worktree branches modify overlapping files | **Sequential merge with conflict check** | Merge branches one at a time, stopping on conflict for operator resolution |
| Changes are independent and low-risk | **Direct merge** | Merge the worktree branch into the active branch |
| Changes are speculative or experimental | **Share only** | Report the branch name to the operator without merging or pushing |

#### Push + PR

```bash
git push origin <branch-name>
# Then use the GitHub MCP server or gh CLI to create a PR
```

#### Direct Merge (from the main working tree)

```bash
cd <main_repo_path>
git merge --no-ff <branch-name> -m "merge: <description>"
```

#### Sequential Merge (multiple branches)

When merging multiple worktree branches that may overlap:

1. Merge the first branch. If clean, continue.
2. Merge the next branch. If conflicts arise, STOP.
3. Report the conflict to the operator with the conflicting file list and branch names.
4. Do NOT auto-resolve conflicts. The operator decides the resolution.
5. After resolution, continue with remaining branches.

#### Post-Merge Verification

After any merge, verify the working tree is clean:

```bash
git status --short
```

If additional isolated work (tests, linting, validation) should run on the merged result before it is considered final, create a new worktree for that verification step rather than running it in the main tree.

### Phase 5: Clean Up

Remove the worktree directory and optionally delete the branch.

#### Who Cleans Up

| Context | Responsible party | Rationale |
| ------- | ----------------- | --------- |
| Subagent completed and merged | **Orchestrator** | Orchestrator owns the lifecycle and has merge context |
| Single-agent isolation (no orchestrator) | **Main agent** | Same agent that created the worktree |
| Branch was pushed/shared for review | **Operator** | Human decides when the branch is no longer needed |
| Parallel execution with orchestrator | **Orchestrator** after all merges | Batch cleanup after all agents finish |

#### Cleanup Commands

```bash
# Remove the worktree
git worktree remove <wt_path> --force

# Delete the branch (only if merged or no longer needed)
git branch -d <branch-name>
# Use -D if the branch was never merged and should be discarded
git branch -D <branch-name>

# Prune stale worktree metadata (in case of unclean removal)
git worktree prune
```

#### Cleanup Rules

- MUST NOT delete a branch that has been pushed to a remote and has an open PR.
- MUST NOT delete a branch whose changes have not been merged or explicitly discarded by the operator.
- SHOULD delete the worktree directory even if the branch is kept (the branch persists in the git object store independent of the worktree).
- SHOULD run `git worktree prune` after removing worktrees to keep metadata clean.

---

## Parallel Execution Pattern

This is the standard pattern for multi-agent parallel work.

### Orchestrator Workflow

1. **Plan**: Decompose the task into independent subtasks. Assign each subtask a unique agent name.
2. **Create**: For each agent, create a worktree (Phase 1) with a unique branch name.
3. **Dispatch**: Launch all agents in parallel. Each agent prompt includes its worktree path and branch name.
4. **Wait**: Monitor agent completion.
5. **Verify**: Check that each agent committed its work. Inspect commit logs on each branch.
6. **Merge**: Apply changes using the decision criteria from Phase 4. Merge sequentially if branches may overlap.
7. **Clean up**: Remove all worktrees and delete merged branches.

### Example: Three Parallel Agents

```text
Orchestrator creates (each branch gets a unique suffix):
  worktree/agent-alpha-a3f1b2  → <base>/my-project--agent-alpha-a3f1b2/
  worktree/agent-beta-7c9e01   → <base>/my-project--agent-beta-7c9e01/
  worktree/agent-gamma-d8e4c1  → <base>/my-project--agent-gamma-d8e4c1/

Orchestrator dispatches agents in parallel:
  Agent Alpha → works in agent-alpha-a3f1b2 worktree
  Agent Beta  → works in agent-beta-7c9e01 worktree
  Agent Gamma → works in agent-gamma-d8e4c1 worktree

Orchestrator merges (sequentially):
  merge worktree/agent-alpha-a3f1b2 → clean
  merge worktree/agent-beta-7c9e01  → conflict detected → report to operator
  (operator resolves)
  merge worktree/agent-gamma-d8e4c1 → clean

Orchestrator cleans up:
  remove all 3 worktrees
  delete all 3 branches
```

---

## Operator-Concurrent Workflow

When the operator wants to keep working while an agent runs in the background:

1. Create a worktree for the agent task.
2. Dispatch the agent to the worktree.
3. The operator continues editing the main working tree freely.
4. When the agent completes, the orchestrator reports the branch name.
5. The operator decides when and how to integrate (merge, cherry-pick, or discard).

This pattern is useful for long-running tasks like test generation, documentation updates, or exploratory refactors.

---

## Validation

**Pass conditions:**

- Worktree created in the correct base directory, not adjacent to the repository
- Branch name follows the `worktree/<purpose>` convention
- Agent operated exclusively within its worktree directory
- Main working tree was not modified during agent execution
- All changes committed on the worktree branch before cleanup
- Merge strategy matches the decision criteria
- Worktree directory removed after merge or discard
- Branch deleted only when safe (merged or explicitly discarded)
- No orphaned worktree metadata remains after cleanup
