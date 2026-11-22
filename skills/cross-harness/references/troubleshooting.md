# Troubleshooting

## Job failed

`xh.py result JOB --json` shows `error`, `exit_code`, and `reason`. The raw output is in
the job directory: `<state home>/jobs/<job>/` holds `result.md`, `result.stdout.log`, and `result.stderr.log`, plus `fix.*` files when a fix step ran.

| Symptom | Likely cause | Action |
|---|---|---|
| `not found on PATH` | CLI not installed, or not on this shell's PATH | Install it, or set `CROSS_HARNESS_<TARGET>_BIN` |
| Auth error in `result.stderr.log` | Target signed out | User runs `codex login` or `claude` and signs in |
| `cannot write the state home` | Caller's sandbox | Rerun with escalated permissions, or set `CROSS_HARNESS_HOME` |
| Network or DNS errors (from Codex calling Claude) | Codex sandbox blocks network | Run `xh.py` with escalated permissions |
| Sandbox errors from Codex (`bwrap`, `CreateProcessAsUserW`, `ACCESS_DENIED`) | Forced sandbox mode unsupported here | Retry with `--sandbox inherit` |
| Model or effort rejected (`model_not_found`, "not supported") | The target's configured default, or the name you passed, isn't available for this CLI version or account (for example an API-only model with a ChatGPT sign-in) | Retry with `--model` set to a model the account supports, or without `--effort`. Tell the user their default is unusable |
| `Failed to open last message file ... path contains a reparse point` (Windows, Codex 0.170+) | Codex's strict output-file open rejected the job directory | Fixed: on Windows, `xh.py` has Codex write `-o` to a temp folder inside the user profile (the default `%TEMP%`) and copies it into the job directory. A temp folder outside the profile may be shared, so then the job directory is used and the error can return: point `TMPDIR` (checked first), or else `TEMP` and `TMP`, at a folder inside the profile that Codex accepts. A job killed mid-run can leave a small `xh-<job>-result-*` folder in the temp folder; it is safe to delete |
| `succeeded` but thin result | Reviewer found nothing, or ran out of turns | Read `result.stdout.log`; narrow the scope with `--focus` |
| `timed_out` | Job exceeded `--timeout` | Narrow the task, or raise `--timeout` |
| `orphaned` | The calling session exited | Expected. Rerun from a live session, or use `--no-owner` |
| `lost` | Supervisor was killed | The sweep already ended its processes; rerun |
| `Nested hand-offs are refused` | Running inside a session this skill started | Expected; don't chain hand-offs |

## Seeing what is running

`xh.py status --all` lists every job with its owner (`(gone)` once the owner exited),
supervisor and child PIDs with liveness, and target directory. Each `xh.py` call also
sweeps jobs whose supervisor vanished. `xh.py cleanup` does the same and removes
records older than 7 days.

## Folders locked by the older Codex plugin for Claude Code

The `openai-codex` plugin (`codex-companion.mjs`) starts a detached
`app-server-broker.mjs` per workspace. The broker has no idle timeout, and only a
clean `SessionEnd` in the same directory stops it. It holds the review directory as
its working directory, along with `codex app-server` and every MCP server Codex starts.
On Windows that makes the folder impossible to delete. This skill does not use or
start brokers, but a machine that ran the plugin may still have them. With the user's
approval, find them and end them:

```powershell
Get-CimInstance Win32_Process |
  Where-Object CommandLine -match 'app-server-broker\.mjs' |
  Select-Object ProcessId, ParentProcessId, CreationDate, CommandLine
# then, per broker the user agrees to stop:
taskkill /PID <pid> /T /F
```

```bash
ps -eo pid,ppid,lstart,args | grep '[a]pp-server-broker.mjs'
kill -- -<pgid>    # or: pkill -f app-server-broker.mjs
```

Uninstalling or disabling that plugin prevents new brokers.

## Posting and PR lookup

| Symptom | Action |
|---|---|
| `cannot tell the review host` | Set `CROSS_HARNESS_REVIEW_HOST=github` or `gitlab` |
| `needs the 'gh' CLI` or `needs the 'glab' CLI` | Install it and sign in (`gh auth login`, `glab auth login`) |
| `no open PR found for the current branch` | Pass `--pr N`, or push the branch and open the PR first |
| `posting failed` | Read the message: usually an expired sign-in or no permission on the repository |
