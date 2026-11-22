# Intent

Let agents rewrite git history (fixups, interactive rebases, amends) reliably without an interactive editor, and without surprising the user on shared branches. Renamed from `git-operations`.

## Goals

1. History rewrites complete without an interactive editor.
2. The user knows which commit changes and confirms before any force-push.
3. Fixups are applied automatically through autosquash, with no manual todo editing.

## Requirements

- Cover interactive rebases, fixup commits, rewording commit messages, squashing, amending, commit splitting, and force-push handling.
- Fixup: `git commit --fixup=<hash>`, applied with a non-interactive `git rebase --autosquash`.
- Interactive rebase: never use `--edit-todo` or rely on the native editor. Edit the todo list file directly, using a `GIT_SEQUENCE_EDITOR` script that inserts `break`.
- Infer the target, clarify when ambiguous, and confirm before rebasing.
- Reworded and new messages follow the repository's commit message conventions.
- Force-push only with explicit user confirmation, using `--force-with-lease`, and warn that collaborators must reset.
- Show the updated history and mark which commits changed.

## Log

- 2026-11-10: Imported into the SkillSinc library layout as `git-operations`. Requirements above are taken from that skill.
- 2026-11-22: [agent] Renamed to `git-history` during the migration to the `skill-development` standard: the skill covers history rewriting only, and "operations" was vague. Rewrote `SKILL.md` from 393 to about 80 lines. Editor setup and troubleshooting moved to `references/`. The editor helpers now use a dated temp file instead of a fixed `/tmp` path, and the todo path uses `git rev-parse --git-path` so it works in worktrees.
- 2026-11-22: [agent] Tested the sequence-editor flow in a scratch repository. `reword` opens `GIT_EDITOR` rather than stopping, so the skill rewords through `edit` plus `git commit --amend -m`. The old skill's claim that the todo file still starts with `break` after the stop was wrong.
- 2026-11-22: [agent] Codex review fixes on the migration: restored confirmation before every rebase; force-push lease pinned to the reviewed remote SHA.
- 2026-11-22: [agent] Second Codex review fixes: the force-push lease SHA is recorded before rewriting, after confirming the remote tip is in local history.
- 2026-11-22: [agent] Third Codex review fixes: Force-push section pins the lease once from the `@{push}` destination (fetch, rev-parse FETCH_HEAD, ancestry check, push the same ref).
- 2026-11-22: [agent] Fourth (final) Codex review fixes: Force-push resolves the push remote and remote ref with `for-each-ref` (not by splitting a tracking ref), stops on a failed ancestry check, and records the values for a fresh shell.
