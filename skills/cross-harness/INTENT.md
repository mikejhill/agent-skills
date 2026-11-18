# Intent

Let Claude Code and Codex hand reviews, prompts, and tasks to each other on explicit
request, without the leaked processes, locked folders, and Windows breakage of the
Codex plugin for Claude Code (`openai/codex-plugin-cc`, unmaintained since 2026-07).

## Goals

1. Nothing outlives its job. A job's whole process tree ends when the job finishes,
   fails, is cancelled, hits its time limit, or its calling session exits, including
   crashes with no clean shutdown. No user directory stays held as a cwd.
2. Both directions with the same guarantees: Codex from Claude Code, and Claude Code
   from Codex.
3. Used only on request. The description stays neutral, and invocation comes from the
   user or their instruction files.
4. Honest about value. Document that cross-model review and delegation help
   sometimes, and that this is not consistently proven.
5. A skill, not a plugin: progressive disclosure, no hooks, no session environment
   writes, harness-neutral layout, stdlib-only Python.
6. Thin over the CLIs: `codex exec` and `codex exec review`, `claude -p`. Pass models,
   efforts, and extra flags through unchanged, so CLI updates don't break the skill.

## Design decisions

- **No broker or daemon.** One CLI process per job. That rules out the largest class
  of upstream bugs: orphaned brokers, shared-broker teardown killing other sessions,
  stale broker reuse, and refresh-token burn from long-lived app-servers.
- **Supervisor per job**, with its cwd in the state home. Windows: the supervisor
  joins a Job Object with `KILL_ON_JOB_CLOSE`, so the OS ends the tree if it dies.
  POSIX: new process group, `PR_SET_PDEATHSIG` on Linux, and a sweep on every
  invocation that kills groups of jobs whose supervisor vanished.
- **Owner watchdog:** the nearest `claude` or `codex` ancestor, checked by pid and
  start time (guards against pid reuse).
- **Start, then wait.** Every caller's shell has a command time limit, so `wait` is a
  restartable poll and killing it never affects the job.
- **Prompts over stdin; the reviewer reads `git` itself.** No size limits, no
  command-line quoting, and no untracked-file or symlink crashes.
- **Per-job state** in a user state home (`%LOCALAPPDATA%` or `XDG_STATE_HOME`),
  keyed by job id and recording owner, target directory, and pids. Never keyed by cwd.
- **Read-only by default.** Write needs `--write`. No `--trust` or bypass flags.
- **One nesting level** (`CROSS_HARNESS_DEPTH`), to stop ping-pong loops.

## Upstream problems addressed

Verified against the upstream source (1.0.6) and its issue tracker, against Mike's
2026-11-14 session report, and on his laptop on 2026-11-18. The last check found a
leaked broker tree of 33 processes holding a deleted review worktree, plus 4 more
orphaned trees.

| Upstream problem | Evidence | Here |
|---|---|---|
| Detached broker with no idle timeout or parent watchdog; stopped only by `SessionEnd` with the same cwd | `broker-lifecycle.mjs` (`detached`, `unref`); #543, #605, #450, #791, #380, #782, #753 | No broker. Job Object or process group, owner watchdog, time limit |
| Broker and app-server hold the review directory as cwd, so Windows can't delete worktrees | session report; laptop check | Supervisor cwd is the state home; the child holds the directory only while it runs |
| App-server never reaps child shells or MCP servers | ~40 to 45 leaked descendants observed | Tree reaped at job end |
| `shell: SHELL \|\| true` on Windows, DEP0190, `.cmd` ENOENT | `app-server.mjs:194`; #32, #46, #67, #85, #832 | Direct spawn of `.exe`, or `node` plus the shim's script |
| `SessionStart` appends env exports without dedup, overflowing Windows' 8191-character limit | #528, #322, #254, #562 | No hooks; no env-file writes |
| Shared broker torn down by one session's end kills others' jobs | #540, #612 | Jobs are independent |
| Jobs stuck `running` after worker death | #164, #222, #517, #639, #698 | Supervisor records every exit path; sweep marks `lost` |
| Bash tool timeout kills foreground runs mid-turn | #542, #634 | Start and wait; the job is detached from the tool call |
| Unbounded prompts and diffs (ENOBUFS, 1 MB limit, EISDIR on untracked) | #11, #405, #69, #14, #65 | Reviewer reads `git` itself; prompt over stdin |
| Hard-coded model and effort lists go stale | #468, #751, #703 | Pass-through |
| Forced sandbox breaks on some platforms | #349, #482, #505, #240 | `--sandbox inherit` |
| Review sessions pollute the user's Codex history | #282 | `--ephemeral` and `--no-session-persistence` |
| Reviewing an untrusted branch loads its hooks and settings | sendbird/cc-plugin-codex#117 | `--isolate` |
| Long-lived app-server burns the single-use ChatGPT refresh token | #789 | Short-lived CLI per job |
| Cleanup needs agents to kill processes, which auto mode blocks | session report | `cancel`, `cleanup`, `status` |

## Fork survey (2026-11-18)

314 public forks were fetched; about 10 carry substantive changes. The most active
(CBEPX, Edo771977, Sjotie, y-cruce, ShallowDream724) spent hundreds of commits on:
broker idle self-termination and verified tree kills; pid-identity checks against
pid reuse; atomic state writes and dead-worker detection; Windows spawn without a
shell; env-file dedup; model and effort pass-through; sandbox overrides; and
declining MCP elicitations that hang headless runs. Most of that complexity
exists to keep a persistent broker alive and correct. This skill drops the broker
instead. The reverse-direction plugin (`sendbird/cc-plugin-codex`) already uses
one `claude -p` per job with the prompt on stdin, which this skill follows.

## Log

- 2026-11-18: [agent] Created from Mike's request and session report. Built `xh.py`
  (supervisor, containment, owner watchdog, sweep, start and wait, resume),
  review prompts, references, and `tests/smoke_test.py` with a fake agent
  (13 lifecycle cases). Live-tested the Claude Code target: adversarial review,
  write task, and resume.
