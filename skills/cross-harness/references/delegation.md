# Delegation

## Writing the brief

The other agent starts with none of your context. Give it everything in the prompt:

- the goal, and what done looks like;
- the relevant files, commands, and constraints (style, tests to run, files not to touch);
- what you already tried or ruled out;
- the shape of the answer you need back (a patch summary, a yes or no with evidence,
  or a list).

Long briefs go through `--prompt-file brief.md` or stdin, never the command line.

## Read-only and write access

| Mode | Codex | Claude Code |
|---|---|---|
| default (read-only) | `exec -s read-only` | read tools only; edits denied |
| `--write` | `exec -s workspace-write`: edits inside `--cwd`, and commands run in Codex's sandbox | `--permission-mode acceptEdits`: edits allowed, Bash limited to read-only `git` |
| `--allow-tools Bash` (Claude only) | n/a | also allows any shell command, with no sandbox |
| `--sandbox inherit` | your `config.toml` decides | no permission flags |

Use `--write` only when the user asked for the other agent to change files. Prefer a
separate git worktree, so its edits stay apart from yours:

```text
git worktree add ../repo-codex-task -b codex/task-name
xh.py task -t codex --write --cwd ../repo-codex-task --prompt-file brief.md
```

Review the diff in that worktree before merging anything back. Remove the worktree
when done. Jobs never hold it after they end.

## Sessions

Tasks keep their session, so you can follow up:

```text
xh.py task -t codex "Investigate why test_x is flaky; report the root cause."
xh.py task -t codex --resume xh-20260101-120000-ab12 "Now propose a fix."
```

`--resume` takes the earlier job id or the target's own session id. Reviews and
`--ephemeral` tasks are not saved and can't be resumed.

## Model and effort

`--model` and `--effort` are passed through unchanged (Codex:
`-m`, `-c model_reasoning_effort=...`; Claude Code: `--model`, `--effort`). Without
them, the target uses its own configured defaults. Use them only when the user names
a model or effort.

## What to return to the user

Say which agent did the work and what it produced. For write tasks, also say which
files changed. If you changed or rejected its output, say so too.
