# git-history

Safe, editor-free recipes for changing existing commits: fixup and autosquash, interactive rebase (reword, edit, split, squash, drop), amend, and force-push.

## Use

Loads automatically when you ask the agent to change commits that already exist. Examples:

- "Fold this fix into the commit that added the parser."
- "Reword the last three commit messages."

## Requirements

- Git. On Windows, Git for Windows (its bundled `sh` runs the rebase helper script).

## Security and side effects

Rewriting pushed commits needs a force-push. The agent asks before any force-push, and uses `--force-with-lease` so it never overwrites commits it has not seen.
