# Troubleshooting history rewrites

| Problem | Fix |
| --- | --- |
| Conflict during a rebase | `git status`, resolve the files, `git add <files>`, `git rebase --continue`. To give up, `git rebase --abort`. |
| Fixup points at the wrong commit, not yet squashed | `git reset --soft HEAD~1`, then `git commit --fixup=<correct-hash>`. |
| Fixup already squashed into the wrong commit | `git reflog`, find the pre-rebase `HEAD`, `git reset --hard <that-sha>` after confirming no other work would be lost, then redo. |
| One fixup mixes changes for several commits | Abort, reset it, and create one fixup per target. Autosquash applies them all together. |
| `Stopped at ...` and nothing seems to happen | That is the inserted `break`. Edit the todo file, then `git rebase --continue`. |
| Rebase hangs waiting for an editor | `GIT_EDITOR` or `core.editor` launched an interactive editor. Abort, set `GIT_EDITOR=true` or pass `-m`, and retry. |
| `--force-with-lease` rejected | The remote moved. Fetch, inspect the new commits, and ask the user how to proceed. Do not switch to `--force`. |
| Autostash conflict after the rebase | Changes are kept in `git stash list`. Resolve and `git stash drop` once applied. |
