# Intent

Help any agent spend fewer, cheaper tool calls on multi-step work, from a timing study
of real browser-automation sessions: model turns (~4 s median per call, ~0.3 s more per
100 command characters) and harness shell spawns (~0.9 s per Bash call, ~1.8 s per
PowerShell call on one Windows machine) dominated, not the commands themselves.

## Goals

1. General, harness-neutral rules for cutting per-call cost: batch predictable steps,
   short commands, bounded output, no discarded output, no sleep-polling, reuse helpers.
2. Shell choice from measurement, not assumption: startup cost varies by machine (Git
   Bash can be slower than PowerShell elsewhere), so the skill measures once per machine,
   caches it, and recommends; task fit still wins over speed.
3. Zero dependencies and cheap to run: one stdlib Python script, a cached answer on
   repeat calls, and a manual fallback without Python.
4. Never change the user's harness settings; recommend only.

## Log

- 2026-11-21: [agent] Created from the browser-control timing study (handoff item 6).
  Operator asked to account for environment-dependent shell performance: Git Bash may
  start slower than PowerShell on other machines. Added `scripts/shell_probe.py` (per-shell
  median/p90 startup, profile cost, per-host cache (7 days; operator cut it from 30), 150 ms "either" threshold) and
  unit tests. Windows check on a real laptop: compare against pwsh 7, not the faster-starting
  Windows PowerShell 5.1 (it had hidden a 171 ms Git Bash vs pwsh gap); report login-shell
  cost; per-process costs in Git Bash and per-process module loads in PowerShell; harness
  overhead can differ per shell.
- 2026-11-22: [agent] Fifth Astra review. PATH skipping covers the whole repository around the
  current directory and links into it; failed shells are part of the cache inventory; WSL launcher
  matched by identity (Sysnative). Documented the trust assumption instead of more path heuristics.
- 2026-11-22: [agent] Sixth Astra review: Git Bash lookup takes bash.exe only (a bash.cmd may forward
  to WSL); SIGTERM/SIGHUP unwind through the sample cleanup; atomic cache write; `either` names
  the faster shell so near-threshold re-runs change strength, not direction; output-bounding
  rule warns that a pipe hides the producer's status; cache tests use stand-in shells.
