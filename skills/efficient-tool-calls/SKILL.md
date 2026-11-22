---
name: efficient-tool-calls
description: Cut the fixed cost of agent tool calls on multi-step work (browser automation, CLI sequences, scripting loops) by batching predictable steps, keeping commands short, bounding output, and choosing the shell measured fastest on this machine. Use when a task will take many shell or tool calls, or when both a POSIX shell and PowerShell are available.
---

# Efficient tool calls

Every tool call has a fixed cost before the command does anything. The model writes the
call and reads the result: in one study, about 4 s of model time per turn, growing ~0.3 s
per 100 characters of command (rough figures; they vary by model and harness). The
harness then runs it, usually in a freshly started shell: 0.1–0.3 s for the shell itself,
and up to ~1 s per call end to end in that study. On a 50-call task the fixed cost is
minutes. Spend fewer, better calls.

## Rules

1. **Batch predictable steps.** Put steps whose outcome you can predict in one call.
   Chain dependent steps with `&&` (PowerShell 7: `&&`; Windows PowerShell 5: `cmd1; if ($?) { cmd2 }`,
   without `2>&1` on `cmd1`, which can make `$?` false on success). Run independent reads in parallel if your harness allows several tool
   calls at once. Stop batching at a point where you need to look at the result to decide,
   and before any step the user must confirm.
2. **Keep commands short.** Call a script file instead of pasting long inline code; reuse
   helper commands a tool already provides instead of re-writing them each call.
3. **Bound output.** Filter at the source (`--max`, `head`, `grep`, `Select-Object
   -First`), so results stay small. Large results cost model time on every later turn.
   In a chain, a pipe reports the filter's status, not the command's: `build | head &&
   next` runs `next` after a failed build, and `head` can cut a producer short. For steps
   whose success matters, use the tool's own limit flag, or save the output and filter it
   afterwards (`build > out.log 2>&1; s=$?; tail -n 40 out.log; test $s -eq 0 && next`).
   `set -o pipefail` fixes the status but not the early stop; use it only with filters
   that read the whole stream.
4. **Don't discard output you need.** Many tools report timeouts, warnings, and partial
   failures on stdout; `>/dev/null`, `| Out-Null`, or merging stderr into a discarded
   stream hides them. Filter instead. Discarding stdout that only ever holds noise is
   fine.
5. **Don't poll with sleeps.** Use a tool's own wait or condition flags, a blocking
   command, or the harness's background/notification feature.
6. **Reuse long-lived helpers.** Prefer a running daemon, broker, or REPL that a tool
   keeps alive over starting one per call.
7. **Mind per-process costs on Windows.** Every extra process in Git Bash costs ~30–40 ms:
   prefer one `grep`/`sed`/`awk` or a short script over long pipelines and `$(...)` loops.
   In PowerShell, the first CIM or web cmdlet in a process loads its module (~0.5–1 s), so
   batch that kind of work into one call.
8. **Avoid login shells** (`bash -l`) unless you need the profile: on one Windows machine
   Git Bash took 675 ms as a login shell and 60 ms without.
9. **Use the faster shell for general work** (below).

## Choosing a shell

Shell startup time depends on the machine, not on the shell's name. Git Bash may start
in 60 ms on one Windows machine and 600 ms on another (antivirus, MSYS emulation,
network home folders); PowerShell 7 may take 0.3 s or 1.5 s with a heavy profile. So
measure once per machine and reuse the answer:

```text
python <skill-dir>/scripts/shell_probe.py   # Windows: python or py -3; else python3
```

`<skill-dir>` is the folder that holds this SKILL.md, not the current workspace.

- It times an empty command in each shell found (bash or zsh, `pwsh`, Windows
  PowerShell, `cmd`), 5 runs after a warm-up, and prints JSON with `median_ms` per
  shell, `fastest_posix`, `fastest_powershell`, and a `recommendation`.
- It compares against PowerShell 7 (`pwsh`) when installed. Windows PowerShell 5.1 often
  starts faster but lacks `&&`, ternaries and UTF-8 defaults; it is reported for
  information only, and isn't a reason to switch.
- The recommendation names the executable it measured (on Windows, Git Bash even when
  `bash` on PATH is the WSL launcher). If your harness starts a different copy, the
  numbers don't apply to it.
- A gap close to 150 ms can come out either side between runs (`either` or `prefer`; both
  name the same faster shell); treat 150–200 ms as a weak
  preference.
- The result is cached per machine for 7 days, so later calls return at once
  (`"cached": true`). `--force` re-measures. The cache is also skipped when the shells found on
  PATH differ from the cached run or `--runs` asks for more samples; re-measure after
  upgrading a shell, changing antivirus, or when calls feel slower than the cache says.
- It runs the shells it finds on PATH. It skips PATH entries inside the current
  repository (or the current directory outside one), but that is best effort: run it from
  a directory you trust, not from an untrusted checkout with an activated environment.
- The baseline runs no startup code: `BASH_ENV` is unset and zsh gets `-f`. If your harness
  sets `BASH_ENV`, add that script's cost. `--profiles` keeps its own cache record.
- With `--profiles`, `profile_cost_ms` appears when loading the PowerShell profile adds 150 ms
  or more, and `login_cost_ms` when a login shell does. They matter only if your harness loads the
  profile for each call.

Then:

| Situation | Do |
|---|---|
| Only one shell tool | Use it; nothing to choose |
| `recommendation` says `either` (under 150 ms apart; it still names the faster shell) | Pick by task; don't switch for speed |
| Your harness starts shells another way (login bash, PowerShell with profile) | Re-run with `--profiles` and compare the matching entries (`bash (login)`, `pwsh (profile)`), with the same 150 ms threshold. It runs your startup scripts several times, including anything they start |
| One shell is faster by 150 ms or more | Use it for general command-line work: `git`, `python`, build and test tools, file reads |
| Work only one shell does well | Use that shell regardless: cmdlets, the registry, .NET and CIM objects in PowerShell; pipes through `grep`/`sed`/`awk` in a POSIX shell |
| Python is not available | Time one empty call per shell by hand and apply the same rule. POSIX: `time bash -c true`. Windows (bare `bash` may be the WSL launcher, so name Git Bash): `Measure-Command { & "$env:ProgramFiles\Git\bin\bash.exe" -c true }` and `Measure-Command { pwsh -NoProfile -c exit }` |

The probe measures bare shell startup. A harness adds its own time per call, and it can
differ per shell (one launches PowerShell through an extra `cmd.exe` hop, ~85 ms; another
sources an environment snapshot in bash, ~15 ms). You can't time a tool call
yourself (the wall time you see includes model latency), so when the probe says `either`
or the gap is near 150 ms, use a per-call time your harness reports if it shows one;
otherwise pick by task.

Don't switch shells in the middle of a dependent sequence to save a few hundred
milliseconds; quoting and path differences cost more than they save.
