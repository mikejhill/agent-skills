---
name: git-operations
description: "Use when performing interactive rebases, fixup commits, rewording commit messages, modifying git history, squashing commits, or amending previous commits. Covers all git history rewriting operations including rebase workflows, fixup commit creation and application, commit splitting, and force-push handling."
---

# Git Operations Skill

## Overview

This skill covers git history rewriting operations: interactive rebase and fixup commits. Use this for any operation that modifies existing commits.

- **Fixup**: Quick way to add small changes to a previous commit; automated during rebase with no user interaction
- **Rebase**: Interactive rebase requiring explicit decisions and manual editing at each step; allows message rewording, structural changes, commit splitting

## Fixup Commits

### When to Use Fixup

Use fixup commits when:

1. You've already committed a change and need to add forgotten files or minor fixes
2. You want to keep your local history clean without amending the original commit
3. You plan to squash all fixups into their target commits before pushing
4. The fix is logically part of the previous commit, not a separate concern

**Do NOT use fixup when:**

- You need to reword the commit message
- You need to split a commit into multiple commits
- You need to reorder commits
- The change is a separate logical concern (create a new commit instead)

### Fixup Workflow

#### Phase 1: Identify Target Commit

1. **Display recent history**:

   ```bash
   git log --oneline -n 10
   ```

2. **Identify which commit needs the fix**:
   - Determine the specific commit hash and subject
   - Confirm with user if necessary: "Should I create a fixup for commit \[hash: subject\]?"

#### Phase 2: Stage and Create Fixup Commit

1. **Make your changes** to files in the working directory

2. **Stage the changes**:

   ```bash
   git add <files>
   # or for selective staging:
   git add -p <file>
   ```

3. **Create fixup commit** (use the exact target commit hash):

   ```bash
   git commit --fixup=<TARGET_COMMIT_HASH>
   ```

   - This creates a commit with message: `fixup! <TARGET_COMMIT_MESSAGE>`
   - Git automatically references the target commit

4. **Verify fixup commit was created**:

   ```bash
   git log --oneline -n 3
   ```

   - Should show: `fixup! <target-message>` as the most recent commit

#### Phase 3: Apply Fixup via Autosquash Rebase (Non-Interactive)

1. **Execute autosquash rebase** (non-interactive mode):

   ```bash
   git rebase --autosquash <TARGET_COMMIT_HASH>~1
   ```

   - Or use: `git rebase --autosquash HEAD~N` where N is how many commits to rebase
   - The `--autosquash` flag automatically moves fixup commits into position and marks them as `fixup`
   - Without `-i`, the rebase runs fully automated without requiring any interactive input

   **EXPECTED OUTPUT**:

   ```text
   Rebasing ...
   Successfully rebased ...
   ```

2. **Git automatically reorders and squashes**:
   - The rebase completes without pausing or user interaction
   - The fixup commit is merged into its target commit
   - The fixup commit's message is discarded
   - The target commit is modified to include the fixup changes

3. **Verify rebase succeeded**:

   ```bash
   git log --oneline -n 5
   ```

   - The fixup commit should no longer appear in history
   - The target commit should now include the changes
   - You should see fewer commits than before (target + fixup → target only)

#### Phase 4: Verify and Push

1. **Verify the squashed commit contains correct changes**:

   ```bash
   git show <SQUASHED_COMMIT_HASH>
   ```

   - Verify that both original content and fixup changes are present

2. **Determine push strategy**:
   - If commits were NOT previously pushed to remote: `git push`
   - If commits WERE previously pushed to remote:
     - Force push is required: `git push --force-with-lease`
     - Get explicit user confirmation before force pushing
     - Warn user that collaborators need to reset their branches

3. **Verify push succeeded**:
   - Check exit code is 0

### Multiple Fixups for Different Commits

If you have multiple fixup commits targeting different commits:

```bash
# Create fixups for different commits
git commit --fixup=<HASH1>  # fixup for commit 1
git commit --fixup=<HASH2>  # fixup for commit 2
git commit --fixup=<HASH1>  # another fixup for commit 1

# Autosquash handles all of them automatically (non-interactive)
git rebase --autosquash <OLDEST_COMMIT>~1

# Result: All fixups are applied to their respective commits
```

The `--autosquash` flag automatically reorders fixups to their correct positions, marks them all as `fixup`, and applies the entire rebase without user interaction.

### Fixup Troubleshooting

**Fixup commit went to wrong commit:**

- Run `git rebase --abort` to cancel
- Verify the target commit hash with `git log --oneline`
- Reset the incorrect fixup commit: `git reset --soft HEAD~1`
- Create a new fixup with correct hash: `git commit --fixup=<CORRECT_HASH>`

**Need to amend the target commit's message:**

- Use the Interactive Rebase section below instead
- Fixup is for changes only, not message modifications

**Fixup contains changes for multiple different concerns:**

- Run `git rebase --abort`
- Create separate fixup commits for each target
- Use autosquash to apply all of them together

**Merge conflicts during autosquash:**

- The rebase will pause automatically
- Run `git status` to identify conflicted files
- Resolve conflicts manually by editing files
- Run `git add <resolved-files>` to stage resolutions
- Run `git rebase --continue` to resume automation

---

## Interactive Rebase

### When to Use Rebase

Use this workflow when fixing a previous commit:

- Renaming commit messages
- Adding missing files to a previous commit
- Fixing commit content
- Splitting a commit into multiple commits

### Rebase Workflow

#### Phase 1: Analyze, Clarify, Confirm

**INFER:**

- Run `git log --oneline -n 10` to display recent commits
- Determine which commit likely needs fixing and what type of fix is needed

**CLARIFY:**

- If the target commit is ambiguous, ask: "Are you referring to \[commit hash/subject\] from 2 commits back?"
- If what needs to be fixed is unclear, ask: "Should I rename the message, add files, or fix content?"
- If the commit has been pushed, note that force push will be required

**CONFIRM:**

- State which commit will be modified, what the fix is, and any force push implications
- Confirm: "Should I proceed with this rebase?"

#### Phase 2: Determine and Execute Fix

##### 1. Determine Fix Type

- **Rename commit message**: Use `reword` action
- **Add missing files**: Use `edit` action, stage files, amend
- **Fix commit content**: Use `edit` action, make changes, amend
- **Split commit**: Use `edit` action, reset, re-commit in parts

##### 2. Start Interactive Rebase

**CRITICAL CONSTRAINT**: Never attempt to use `--edit-todo` or rely on the native editor. The native editor will not be available. Instead, you MUST edit the todo list file directly using file manipulation commands.

**Setup Direct Todo List Editing (Required):**

Create a temporary editor script that allows direct file manipulation without opening an interactive editor:

```powershell
# PowerShell
$EditorScript = @'
#!/bin/sh
printf 'break\n' > "$1.new"
cat "$1" >> "$1.new"
mv "$1.new" "$1"
'@
$ScriptPath = Join-Path $env:TEMP "git-rebase-editor.sh"
Set-Content -Path $ScriptPath -Value $EditorScript -NoNewline
$env:GIT_SEQUENCE_EDITOR = $ScriptPath.Replace('\', '/').Replace(' ', '\ ')
```

```bash
# Bash
cat > /tmp/git-rebase-editor.sh << 'EOF'
#!/bin/sh
printf 'break\n' > "$1.new"
cat "$1" >> "$1.new"
mv "$1.new" "$1"
EOF
chmod +x /tmp/git-rebase-editor.sh
export GIT_SEQUENCE_EDITOR="/tmp/git-rebase-editor.sh"
```

**Execute Rebase:**

- Run `git rebase -i --autostash <commit-hash>~1` (where `<commit-hash>` is the target commit)
- Or use `git rebase -i --autostash HEAD~N` where N is how many commits back
- Git will automatically invoke the custom editor script, which inserts a `break` command at the start of the rebase
- **EXPECTED OUTPUT** (indicates rebase started successfully):

  ```text
  Created autostash: <object-hash>
  Stopped at <commit-hash> (<commit-message>)
  ```

- This output means the rebase has **successfully started** and is paused at the `break` command
- **Locate the todo list file**: `.git/rebase-merge/git-rebase-todo` (relative to repository root)
- Read the todo list file directly using: `Get-Content .git/rebase-merge/git-rebase-todo` (PowerShell) or `cat .git/rebase-merge/git-rebase-todo` (Bash)
- The file will contain lines like:

  ```text
  break
  pick <hash> <commit message>
  pick <hash> <commit message>
  ```

- Edit the todo list file directly (do NOT use `--edit-todo` or open any editor) to change `pick` to the desired action:
  - `reword` for renaming commit message only
  - `edit` for adding files or modifying content
  - `fixup` or `squash` if combining commits
- Run `git rebase --continue` to execute the rebase with your modifications

##### 3. Execute Fix

**For `reword`:**

- Understand what needs to be reworded (analyze the current message and what should change)
- Construct new message following the commit message template from the git commit conventions instructions
- MUST follow all formatting rules (50 char subject, 72 char body wrap, etc.)
- Confirm the proposed new message before applying
- Run `git commit --amend -m "<new-message>"`
- Run `git rebase --continue`

**For `edit` (adding missing files):**

- Git pauses at the commit
- Run `git add <files>` to stage missing files (or `git add -p <file>` for selective staging)
- Run `git commit --amend --no-edit` to add files without changing message
- Verify with `git show --stat` to confirm files are included
- Run `git rebase --continue`

**For `edit` (fixing content):**

- Git pauses at the commit
- Make necessary changes to files
- Run `git add <files>` to stage changes (or `git add -p <file>` for hunk-level staging)
- Run `git commit --amend` to update commit (edit message if needed)
- Verify with `git show` to confirm changes are correct
- Run `git rebase --continue`

**For `edit` (splitting commit):**

- Git pauses at the commit
- Run `git reset HEAD~1` to unstage all changes (files remain modified)
- Verify all changes are unstaged with `git status`
- Create multiple commits following standard commit workflow
- Each new commit MUST follow the commit message template
- Use `git add -p` to select relevant hunks for each commit
- After all commits are created, run `git rebase --continue`

#### Phase 3: Verify and Push

1. **Verify Rebase**:
   - Run `git log --oneline -n 10` to display updated history
   - Show the updated commit history to user
   - Confirm with user that commit history is correct before pushing

2. **Push Changes**:
   - If commits were NOT previously pushed to remote: Run `git push`
   - If commits WERE previously pushed to remote:
     - Explain to user that force push is required because history was rewritten
     - Warn that collaborators who have pulled these commits will need to reset their branches
     - Get explicit user confirmation with "Yes" before proceeding
     - Run `git push --force-with-lease` (safer than `--force`)
   - Verify push succeeded by checking exit code

3. **Report**:
   - Display updated commits in table format
   - Mark which specific commits were modified during rebase

---

## Quick Reference

### Fixup Commands

| Task                               | Command                              |
| ---------------------------------- | ------------------------------------ |
| Create fixup for commit            | `git commit --fixup=<HASH>`          |
| Apply all fixups (non-interactive) | `git rebase --autosquash <OLDEST>~1` |
| Abort rebase if wrong              | `git rebase --abort`                 |
| View squashed result               | `git show <HASH>`                    |
| Force push after rebase            | `git push --force-with-lease`        |

### Interactive Rebase Actions

```text
pick  = use commit as-is
reword = use commit, but edit the commit message
edit = use commit, but stop for amending (add files, change content)
squash = use commit, but meld into previous commit
fixup = like squash, but discard this commit's message
drop = remove commit
```

### Typical Rebase Workflow

1. `git rebase -i HEAD~3` (if commit is 3 back)
2. Change `pick` to `edit` for target commit
3. Save and close editor
4. Git pauses at that commit
5. `git add <missing-file>`
6. `git commit --amend --no-edit`
7. `git rebase --continue`
8. `git push --force-with-lease` (if already pushed)

### Abort

```bash
git rebase --abort
```

## Validation

**Pass Conditions:**

- Fixup commit created with `--fixup=<HASH>` pointing to correct target
- Autosquash rebase executed without user intervention errors
- Fixup commit message follows pattern: `fixup! <TARGET_MESSAGE>`
- After rebase, fixup commit no longer appears in history
- Target commit contains both original and fixup changes
- Each fixup applied to correct target commit
- During rebase, todo list was edited directly (never used `--edit-todo` or native editor)
- Force push (if required) received explicit user confirmation
- Each commit message follows the template format
