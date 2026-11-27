---
description: Run Codex's own code review on local git state through cross-harness
argument-hint: "[--base <ref> | --commit <sha> | --uncommitted | --pr <n>] [--fix] [--post] [--model <m>] [--effort <e>]"
---

# Codex Review

Run a Codex review with the `cross-harness` skill (load it first). The script is
normally `~/.claude/skills/cross-harness/scripts/xh.py`.

Arguments: `$ARGUMENTS`

1. Run `xh.py review -t codex $ARGUMENTS`. With no scope argument, the review covers
   uncommitted changes. If the user named a branch or PR in words, pass `--base` or
   `--pr`.
2. Poll with `xh.py wait <job> --timeout 90`, repeating while the exit code is 3.
3. Show Codex's findings in full, then your own check of each one: confirmed,
   refuted with the reason, or unclear. Fix nothing unless `--fix` was passed or
   the user asks.
