# Caller notes

## Calling from Claude Code

- The Bash tool stops a command after 2 minutes by default (10 minutes at most) and
  can move long commands to the background. `xh.py review` and `task` return at
  once, and `wait --timeout 90` stays under the default. Keep each `wait` under the
  limit and call it again on exit code 3. Never run the target CLI directly in a
  long foreground command.
- Auto mode or permission rules may ask before running `python .../xh.py`. That is
  expected: the command starts another agent.
- The job's owner is the `claude` process. When that session ends, its jobs are ended
  too.

## Calling from Codex

- Codex's sandbox blocks network access and writes outside the workspace by default.
  The Claude Code CLI needs the network, and `xh.py` writes its state home outside the
  workspace. Run `xh.py` commands with escalated permissions (request approval to run
  outside the sandbox), and explain to the user that the command starts Claude Code.
  `check` reports a state home that isn't writable.
- Codex ends shell commands after its own timeout. Give `xh.py wait` a timeout below
  it, or pass a longer command timeout, and repeat `wait` while it returns 3.
- The job's owner is the `codex` process.

## Windows

- `xh.py` starts `codex.exe` or `claude.exe` directly. For npm installs it runs the
  package's script with `node`. It never goes through `cmd.exe` or a shell, so the
  `SHELL` and Git Bash settings don't matter and Node's DEP0190 warning can't appear.
- The supervisor runs windowless (`pythonw` when available) and puts itself and every
  process it starts in a Job Object with kill-on-close. If the supervisor dies for any
  reason, Windows ends the whole tree, including MCP servers and shells that the
  agent started.
- The state home is `%LOCALAPPDATA%\agent-skills\cross-harness` on Windows, `~/Library/Caches/agent-skills/cross-harness` on macOS, and `${XDG_CACHE_HOME:-~/.cache}/agent-skills/cross-harness` on Linux. Set `CROSS_HARNESS_HOME` to move it.

## Environment

The child gets the caller's environment, minus the variables that tie a process to
the calling session (`CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SSE_PORT`,
`CLAUDE_ENV_FILE`, `CODEX_SANDBOX*`, `CODEX_THREAD_ID`), plus `CROSS_HARNESS_DEPTH`
(the nesting guard) and `CROSS_HARNESS_JOB`. Nothing is written to either harness's
settings, hooks, or session environment files.

`CROSS_HARNESS_CODEX_BIN` and `CROSS_HARNESS_CLAUDE_BIN` override CLI discovery.
