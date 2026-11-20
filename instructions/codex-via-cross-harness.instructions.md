---
name: Codex review gate
description: Claude Code only. Run a Codex review of your code changes before you finish a task, through the cross-harness skill.
applyTo: "**"
---

# Codex review gate

Before you report a task as done, have Codex review the code you changed. This replaces
the openai-codex plugin's stop-time review gate.

## When

- Run the gate once per task, after your last code edit and before your final reply.
  Don't run it after every intermediate step.
- Skip it when the task changed no code: questions, research, plans, status checks,
  reviews, or edits to prose and docs only.
- Skip it when `CROSS_HARNESS_DEPTH` is set in the environment. That means Codex
  started this session, and a review would loop back.
- Skip it when the user says to skip it for this task or session.
- If `xh.py check -t codex` shows Codex missing or signed out, skip the gate and say so
  once in your reply.

## How

Use the `cross-harness` skill (load it for the workflow). The script is normally
`~/.claude/skills/cross-harness/scripts/xh.py`.

1. Pick the scope of this task's changes: `--uncommitted` while they are uncommitted, or
   `--base <branch's base>` once they are committed on a feature branch.
2. Run `xh.py review -t codex --adversarial <scope>`. Then run
   `xh.py wait <job> --timeout 90`, repeating while the exit code is 3.
3. Check each finding against the code. Fix the confirmed ones that would block shipping
   (correctness, security, data loss, or broken behavior). Leave refuted and minor ones
   unfixed, and list them.
4. If you fixed anything, run the gate once more on the new state. Stop after two review
   rounds, and report anything still open instead of looping.
5. In your final reply, add a short "Codex review" section: what it found, what you
   fixed, and what you rejected and why.

If a review fails or times out, say so in your reply and finish anyway. Never let the
gate block the task indefinitely.

## Related

The `/codex-review`, `/codex-adversarial-review`, `/codex-rescue`, `/codex-status`,
`/codex-result`, and `/codex-cancel` commands run the same tools on demand.
