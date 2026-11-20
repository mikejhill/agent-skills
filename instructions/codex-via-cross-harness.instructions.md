---
name: Codex review gate
description: Claude Code only. Run a Codex review automatically on every change before finishing, through the cross-harness skill.
applyTo: "**"
---

# Codex review gate

Get a Codex review automatically before you finish any turn that changed files in a
Git repository. The user doesn't need to ask. This rule is that request, so the
`cross-harness` skill's "explicit request only" condition is met. Load that skill
for its workflow. The script is normally `~/.claude/skills/cross-harness/scripts/xh.py`.

## When to run it

- Run it after the change is finished and your own checks pass. Run it before you
  report completion, commit, push, or merge.
- Skip it when the turn changed no tracked or new files in a repository. A chat
  answer, a read-only investigation, or edits outside any repository don't qualify.
- Skip it when the user says to skip it for the task. Skip it in a session that
  another agent started through cross-harness (`claude -p` from Codex).

## How to run it

1. Start the review on the scope of your change:
   - uncommitted work: `xh.py review -t codex --uncommitted --cwd <repo>`
   - committed work on a branch: `xh.py review -t codex --base <default-branch> --cwd <repo>`
2. Poll with `xh.py wait <job> --timeout 90`, repeating while the exit code is 3.
   Keep each call under the shell tool's time limit.
3. Check each finding against the code: confirmed, refuted with the reason, or
   unclear. Fix the confirmed ones, and rerun your own checks.
4. If you changed code in step 3, run one more review on the new state. Stop after
   two review rounds in a turn. Report anything still open instead of looping.

## What to report

In your final message, show Codex's findings in a short list, each with your
verdict, and say what you fixed. If the review failed or timed out, say so and give
the job ID. Never present Codex's output as the verdict.

If Codex is unavailable (`xh.py check -t codex` fails), say so once and finish
without the review.

## Manual commands

`/codex-review`, `/codex-adversarial-review`, `/codex-rescue`, `/codex-status`,
`/codex-result`, and `/codex-cancel` run the same script on demand.
