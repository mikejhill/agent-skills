---
name: efficient-tool-calls
description: Cut the fixed cost of agent tool calls on multi-step work (browser automation, CLI sequences, scripting loops) by batching predictable steps, keeping commands short, bounding output, and choosing the shell measured fastest on this machine. Use when a task will take many shell or tool calls, or when both a POSIX shell and PowerShell are available.
---

# Efficient tool calls

Every tool call has a fixed cost before the command does anything: the model writes the
call and reads the result (about 3–4 s of model time per turn, growing ~0.3 s per 100
characters of command), and the harness usually spawns a fresh shell for it (about 1 s,
more for a slow shell). On a 50-call task that fixed cost is minutes. Spend fewer, better
calls.

## Rules

1. **Batch predictable steps.** Put steps whose outcome you can predict in one call.
   Chain dependent steps with `&&` (PowerShell 7: `&&`; Windows PowerShell 5: `;` plus
   `if ($?)`). Run independent reads in parallel if your harness allows several tool
   calls at once. Stop batching at a point where you need to look at the result to decide,
   and before any step the user must confirm.
2. **Keep commands short.** Call a script file instead of pasting long inline code; reuse
   helper commands a tool already provides instead of re-writing them each call.
3. **Bound output.** Filter at the source (`--max`, `head`, `grep`, `Select-Object
   -First`), so results stay small. Large results cost model time on every later turn.
4. **Don't discard output you need.** `>/dev/null` or `| Out-Null` on an action hides its
   errors and timeouts; filter it instead.
5. **Don't poll with sleeps.** Use a tool's own wait or condition flags, a blocking
   command, or the harness's background/notification feature.
6. **Reuse long-lived helpers.** Prefer a running daemon, broker, or REPL that a tool
   keeps alive over starting one per call.
7. **Use the faster shell for general work** (below).

## Choosing a shell

Shell startup time depends on the machine, not on the shell's name. Git Bash may start
in 60 ms on one Windows machine and 600 ms on another (antivirus, MSYS emulation,
network home folders); PowerShell 7 may take 0.3 s or 1.5 s with a heavy profile. So
measure once per machine and reuse the answer:

```text
python scripts/shell_probe.py          # Windows: python or py -3; else python3
```

- It times an empty command in each shell found (bash or zsh, `pwsh`, Windows
  PowerShell, `cmd`), 5 runs after a warm-up, and prints JSON with `median_ms` per
  shell, `fastest_posix`, `fastest_powershell`, and a `recommendation`.
- The result is cached per machine for 30 days, so later calls return at once
  (`"cached": true`). `--force` re-measures; re-measure after installing or upgrading a
  shell, changing antivirus, or when calls feel slower than the cached numbers say.
- `profile_cost_ms` appears when loading the PowerShell profile adds 150 ms or more.
  That matters only if your harness loads the profile for each call.

Then:

| Situation | Do |
|---|---|
| Only one shell tool | Use it; nothing to choose |
| `recommendation` says `either` (under 150 ms apart) | Pick by task; don't switch for speed |
| One shell is faster by 150 ms or more | Use it for general command-line work: `git`, `python`, build and test tools, file reads |
| Work only one shell does well | Use that shell regardless: cmdlets, the registry, .NET and CIM objects in PowerShell; pipes through `grep`/`sed`/`awk` in a POSIX shell |
| Python is not available | Time one empty call per shell by hand (`time bash -c true`; `Measure-Command { pwsh -NoProfile -c exit }`) and apply the same rule |

The probe measures shell startup only. The harness adds its own fixed time per call on
top of it, the same for each shell, so the difference between shells is what the probe
reports.

Don't switch shells in the middle of a dependent sequence to save a few hundred
milliseconds; quoting and path differences cost more than they save.
