---
description: Run an adversarial Codex review that challenges the change, through cross-harness
argument-hint: "[--base <ref> | --commit <sha> | --uncommitted | --pr <n>] [--fix] [--post] [focus text ...]"
---

# Codex Adversarial Review

Run an adversarial Codex review with the `cross-harness` skill (load it first). The
script is normally `~/.claude/skills/cross-harness/scripts/xh.py`.

Arguments: `$ARGUMENTS`

1. Split the arguments: flags (`--base`, `--commit`, `--uncommitted`, `--pr`,
   `--fix`, `--post`, `--model`, `--effort`) stay flags. Any remaining free text
   becomes `--focus "<text>"`.
2. Run `xh.py review -t codex --adversarial <flags> [--focus "<text>"]`.
3. Poll with `xh.py wait <job> --timeout 90`, repeating while the exit code is 3.
4. Show the findings in full, then your own check of each one: confirmed, refuted
   with the reason, or unclear.
