---
name: cross-harness
description: >-
  Run a code review, prompt, or task in the other coding-agent CLI (Codex from
  Claude Code, or Claude Code from Codex) and collect the result, with bounded,
  self-cleaning processes. Use only when the user or their instructions
  explicitly ask to involve the other agent.
compatibility: Claude Code or Codex, with the other agent's CLI installed and signed in. Python 3.8+.
---

# Cross-harness

Hand a review, prompt, or task from the current agent to the other one: Claude Code
(`claude`) or Codex (`codex`). Use it only on an explicit request. A user might write
"have Codex review this" or "ask Claude to try this prompt", or an instruction file
might say "get a Codex review on every PR before marking it ready". Don't reach for it
on your own initiative.

> **Caveat: the benefit is not proven.** A second model can catch defects the first
> missed, and an adversarial pass can expose weak assumptions. The evidence is mixed,
> though. Cross-model reviews also produce confident false positives, can miss what both
> models are blind to, and double the cost and time. Treat the other agent's output as a
> second opinion to verify, never as a verdict. Tell the user the same if they ask
> whether it is worth it.

## How it works

`scripts/xh.py` (Python 3.8+, stdlib only) runs each job as **one** short-lived CLI
process (`codex exec` or `claude -p`) under a small supervisor. No daemon or shared
server runs, and nothing is installed into either harness. The supervisor:

- holds no user directory as its working directory;
- contains the whole process tree (a Windows Job Object; a POSIX process group);
- ends that tree when the job finishes, fails, is cancelled, hits its time limit
  (default 30 min), or when the calling `claude` or `codex` process exits.

```text
python scripts/xh.py <command> ...     # Windows: py -3 or python
```

Paths are relative to this skill's directory.

## Workflow

1. **Check once per session:** `xh.py check -t codex` (or `-t claude`). It reports the
   CLI path, version, sign-in state, and whether the state home is writable. If the
   CLI is missing or signed out, tell the user and stop.
2. **Start:** `xh.py review ...` or `xh.py task ...` prints `{"job": "xh-..."}` and
   returns at once. The job runs in the background.
3. **Wait:** `xh.py wait JOB --timeout 90`. It returns 0 with the result when the job
   succeeds, 1 when it fails, and 3 when it is still running. On 3, call `wait` again.
   Keep `--timeout` below your own shell-command time limit (see
   [caller notes](references/caller-notes.md)). An interrupted `wait` never affects
   the job.
4. **Use the result:** verify it before acting on it (see below), then report to the
   user what the other agent said and what you concluded.

## Commands

| Command | Purpose |
|---|---|
| `check [-t T]` | CLI path, version, sign-in, state home |
| `review -t T [--base REF \| --commit SHA \| --uncommitted \| --pr N] [--native-args "..."] [--fix] [--post]` | Run the target's own reviewer; optionally fix and post |
| `review ... --adversarial` / `--focus TEXT` | The skill's review prompt instead of the native reviewer |
| `task -t T [--write] [--resume JOB] "prompt"` (or `--prompt-file F`, or stdin) | Hand over a prompt or task |
| `wait JOB [--timeout S]` / `result JOB` | Get the outcome |
| `status [--all] [JOB]` | Jobs with owner, PIDs, liveness, and target directory |
| `cancel JOB` / `cancel --all` | End a job and its whole process tree |
| `cleanup [--dry-run] [--prune-days N]` | Sweep lost jobs and prune old records |

Common options for `review` and `task`: `--cwd DIR` (the repository; default is the
current directory), `--model`, and `--effort`. Both pass through unchanged, so new
model names work without edits here. Also: `--timeout MIN`, `--wait S` (start and
wait in one call), `--isolate`, `--label`, `--extra ARG` (raw CLI argument, repeatable),
and `--json`.

## Reviews

By default `review` runs the target's **own** reviewer and lets it behave as it
normally does:

- Codex: `codex exec review` (the headless form of `/review`), scoped by `--base`,
  `--commit`, `--uncommitted`, or `--pr`.
- Claude Code: `/code-review` in `claude -p`. `--native-args "high --max-findings all"`
  is appended verbatim, so its levels and flags keep working as they change.

`--fix` applies fixes. Claude fixes inside its own review (`/code-review --fix`). For
Codex the skill runs a second, write-enabled step that gets the findings. `--post`
publishes the review to the PR or MR: Claude uses its own `--comment`, and otherwise
the skill posts one summary comment with `gh` (GitHub) or `glab` (GitLab). `--pr N`
picks the PR or MR. Without it, the current branch's is used.

`--adversarial` or `--focus "..."` switch to the skill's own review prompt, which is
read-only. `--fix` and `--post` still work as follow-up steps.

Before relaying findings, check each one against the code. Say which you confirmed,
which you refuted and why, and fix only what the user asked for. Posting and fixing
change things outside the conversation, so do either only when the user or their
instructions ask. Details: [reviews](references/reviews.md).

## Tasks

`task` is read-only by default: the other agent can read and answer but not edit.
`--write` lets it edit inside `--cwd`. Use `--write` only when the user asked for the
other agent to make changes, and prefer a separate worktree for it. `--resume JOB`
continues an earlier task's session. Write a self-contained brief: the other agent
sees none of your conversation. Details: [delegation](references/delegation.md).

## Rules

- Never pass `--trust`, `--dangerously-*`, or `--sandbox danger-full-access` through
  `--extra` unless the user explicitly asked for it.
- One hand-off level only. A session started by this skill refuses to start another
  (`--allow-nested` overrides that, on explicit request only).
- Don't kill processes by hand. Use `cancel`, `cleanup`, and `status` instead.
- Jobs end when the calling session ends. `--no-owner` lets a job outlive it, still
  bounded by `--timeout`. Use it only when the user wants that.

## References

- [reviews.md](references/reviews.md): review modes, prompts, and handling findings
- [delegation.md](references/delegation.md): briefs, write access, worktrees, and resume
- [caller-notes.md](references/caller-notes.md): calling from Claude Code, calling from
  Codex (sandbox escalation), and Windows
- [troubleshooting.md](references/troubleshooting.md): failures, stuck jobs, and
  folders locked by the older Codex plugin
