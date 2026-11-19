---
name: Codex via cross-harness
description: Claude Code only. Route requests to involve Codex through the cross-harness skill.
applyTo: "**"
---

# Codex via cross-harness

When the user, or an instruction file, asks to involve Codex (a Codex review, an
adversarial review, a second opinion, or a delegated task), use the `cross-harness`
skill's `scripts/xh.py` with `-t codex`. The script is normally at
`~/.claude/skills/cross-harness/scripts/xh.py`. Load that skill first for its workflow.
The `/codex-review`, `/codex-adversarial-review`, `/codex-rescue`, `/codex-status`,
`/codex-result`, and `/codex-cancel` commands are shortcuts for the same calls.

- Don't use the `openai-codex` plugin (`codex-companion.mjs`, `/codex:*`) even if it
  is still installed. It leaks background processes that lock folders.
- Don't involve Codex unless asked.
- Start the job, then poll it with `xh.py wait JOB --timeout 90`. Repeat while the
  exit code is 3, keeping each call under the Bash time limit.
- Present Codex's output, then your own check of it: confirmed, refuted with the
  reason, or unclear. Never present it as the verdict.
