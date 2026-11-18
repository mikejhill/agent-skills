# Reviews

## Choosing the scope

| Want | Command |
|---|---|
| Branch or PR against its base | `xh.py review -t codex --base main` |
| One commit | `xh.py review -t codex --commit abc123` |
| Uncommitted work (staged, unstaged, untracked) | `xh.py review -t codex` |
| Attack-minded pass | add `--adversarial` |
| Steer the reviewer | add `--focus "concurrency in the cache layer"` |
| A repository other than the current directory | add `--cwd PATH` |

For a PR, check out its head branch (or a worktree of it) and review against the
PR's base branch. Fetch the base first, so `--base origin/main` is current.

## What runs

| Target | Plain review | `--focus` or `--adversarial` |
|---|---|---|
| Codex | `codex exec review --base/--commit/--uncommitted` (built-in reviewer, read-only sandbox, `--ephemeral`) | `codex exec -s read-only --ephemeral` with the prompt from `assets/prompts/` |
| Claude Code | `claude -p --no-session-persistence` with the prompt from `assets/prompts/`, read-only tools (Read, Grep, Glob, read-only `git`), and edit tools denied | same |

The reviewer reads the diff itself with `git`, so large diffs and untracked files never
go through a command line or a prompt-size limit. Prompts go over stdin.

`--isolate` keeps the reviewed checkout's own agent configuration out of the review
where the CLI allows it: Claude Code loads only user settings (no project hooks or
permissions), and Codex ignores execpolicy rules. Use it when reviewing a branch you
do not trust. Instruction files (`CLAUDE.md`, `AGENTS.md`) are still read by both.

`--sandbox inherit` drops the read-only sandbox flag for Codex and uses the sandbox in
your own `config.toml`. Use it when the forced sandbox fails on your platform, for
example a Linux kernel that blocks unprivileged user namespaces.

## Handling findings

The reviewer's output is a claim, not a fact.

1. Read every finding against the code. Confirm or refute it from the source, and
   run a test when that is cheap.
2. Sort the findings into confirmed, refuted (with the reason), and unclear.
3. Report all three groups to the user. Don't silently drop a finding you disagree
   with. Say why it doesn't hold.
4. Fix only what the user asked you to fix. "Review and fix" covers confirmed
   findings. "Get a review" means report only.
5. If the reviewer and you still disagree after checking, the user decides.

A clean review ("No material findings") is weak evidence. Say what scope was reviewed,
and don't present it as proof of correctness.

## Recurring review instructions

A user instruction such as "run a Codex adversarial review on every PR before marking
it ready" means:

```text
xh.py review -t codex --base <PR base> --adversarial --label "PR #<n>"
xh.py wait <job> --timeout 90          # repeat while exit code is 3
```

Verify the findings, fix the confirmed ones if that is part of the instruction, then
mark the PR ready and summarize the review in the PR or your reply.
