---
name: git-history
description: >-
  Rewrite git history safely without an interactive editor: fixup commits,
  autosquash, interactive rebase (reword, edit, split, squash, drop), amend,
  and force-push. Use when changing commits that already exist.
---

# Git history

Change existing commits with predictable, non-interactive commands, and confirm before anything that affects a shared branch.

## Pick the operation

| Need | Operation |
| --- | --- |
| Add a small forgotten change to an earlier commit | Fixup + autosquash |
| Change the last commit only | `git commit --amend` |
| Reword a message, split, reorder, squash, or drop commits | Interactive rebase |
| A separate logical change | A new commit, not a rewrite |

## Rules

- Show `git log --oneline -n 10`, name the target commit by hash and subject, and ask when it is ambiguous.
- Before any rebase, show the proposed changes (which commits are reordered, squashed, dropped, or reworded) and get the user's confirmation.
- Never open an editor. Interactive editors are unavailable to agents. Set `GIT_SEQUENCE_EDITOR` and edit the todo file directly ([rebase-editor.md](references/rebase-editor.md)). Never use `--edit-todo`.
- Use `--autostash` on rebases when the working tree is dirty.
- New or reworded messages follow the repository's commit conventions.
- If the rewritten commits were already pushed, explain that a force-push is needed and that collaborators must reset. Get the user's explicit yes, then pin the lease to the remote tip you showed them: `git push --force-with-lease=<branch>:<reviewed-remote-sha>`, never `--force`. A bare `--force-with-lease` compares against the remote-tracking ref, which a background fetch can update.
- If anything goes wrong mid-rebase, `git rebase --abort` restores the original state.

## Fixup and autosquash

```bash
git add <files>                          # or git add -p <file>
git commit --fixup=<target-hash>         # creates "fixup! <target subject>"
git rebase --autosquash <oldest-target>~1   # Git 2.44+; runs without stopping
git log --oneline -n 5                   # fixup commits are gone
git show <new-target-hash>               # target holds both changes
```

Before Git 2.44, `--autosquash` needs `-i`: run `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <oldest-target>~1`. Several fixups for different targets apply in one autosquash rebase from the oldest target. A fixup carries changes only. To change a message, use a rebase `edit` stop.

## Interactive rebase

1. Set the sequence editor so the rebase stops before the first commit ([rebase-editor.md](references/rebase-editor.md)).
2. Start: `git rebase -i --autostash <target-hash>~1`. Expect `Stopped at ...` from the inserted `break`.
3. Edit `.git/rebase-merge/git-rebase-todo` (in a worktree, `$(git rev-parse --git-path rebase-merge/git-rebase-todo)`): change `pick` to `edit`, `fixup`, or `drop`, or reorder lines. To reword, use `edit`: `reword` opens `GIT_EDITOR`, which an agent cannot drive.
4. `git rebase --continue`, then handle each stop:

| Action | At the stop |
| --- | --- |
| `edit`, reword | `git commit --amend -m "<message>"` |
| `edit`, add files | `git add <files>`, `git commit --amend --no-edit`, check with `git show --stat` |
| `edit`, fix content | Change files, `git add`, `git commit --amend --no-edit`, check with `git show` |
| `edit`, split | `git reset HEAD~1`, then commit each part with `git add -p` |

After each stop, `git rebase --continue`.

Then show the new `git log --oneline` and mark which commits changed. Confirm with the user before pushing.

## References

- [rebase-editor.md](references/rebase-editor.md): read before any interactive rebase. It has the sequence-editor setup for Bash and PowerShell.
- [troubleshooting.md](references/troubleshooting.md): read on conflicts, a fixup aimed at the wrong commit, or a stuck rebase.
