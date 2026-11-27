---
name: Codex review gate
description: Claude Code only. In repositories where the user turned on the Codex review gate, get a Codex review of each turn's code edits before finishing, through the cross-harness skill.
applyTo: "**"
---

# Codex review gate

This mirrors the openai-codex plugin's stop-time review gate. It is off by default,
and the user turns it on for one repository at a time. In a repository where it is
on, get a Codex review of each turn's code edits before you finish that turn. The
user turning the gate on is the explicit request that the `cross-harness` skill
requires. Load that skill for its workflow. The script is normally
`~/.claude/skills/cross-harness/scripts/xh.py`.

## Turning it on and off

The setting lives in the repository's local Git config, which is never committed. It
covers every worktree of the repository.

| User says | Run in the repository |
|---|---|
| "enable the Codex review gate" (or similar) | `git config --local cross-harness.reviewGate true` |
| "disable the Codex review gate" | `git config --local --unset cross-harness.reviewGate` |
| "is the Codex review gate on?" | `git config --get cross-harness.reviewGate` |

When you turn it on, tell the user what the plugin's README warns: the gate costs a
Codex run on every editing turn and can drain usage limits quickly.

## When it runs

Run it at the end of a turn only when all of these hold:

- `git config --get cross-harness.reviewGate` prints `true` in the repository you
  edited.
- You made direct code edits in this turn. These don't count: status checks, setup,
  summaries, review results, answers, read-only investigation, and edits made in
  earlier turns.
- `CROSS_HARNESS_DEPTH` is not set (Codex didn't start this session).
- The user hasn't said to skip it for this turn or task.

Run it after your own checks pass, and before you report completion, commit, push,
or merge.

## How to run it

1. Start an adversarial review of this turn's edits:
   `xh.py review -t codex --adversarial --uncommitted --cwd <repo> --focus "Only the edits Claude made in its last turn: <files and one-line summary>. Challenge whether they should ship."`
   If you committed this turn's edits, use `--commit <sha>` instead of `--uncommitted`.
2. Poll with `xh.py wait <job> --timeout 90`, repeating while the exit code is 3.
3. Check each finding against the code and mark it confirmed, refuted with the reason,
   or unclear. Fix the confirmed findings that block shipping, and rerun your checks.
4. If you fixed anything, review once more. The plugin loops until Codex allows the
   stop. This gate stops after two rounds in a turn and reports anything still open.

## What to report

End with a short "Codex review" list: each finding, your verdict, and what you fixed.
If the review failed or timed out, give the job ID and finish anyway. Never present
Codex's output as the verdict. If `xh.py check -t codex` fails, say once that the gate
was skipped.

## Manual commands

`/codex-review`, `/codex-adversarial-review`, `/codex-rescue`, `/codex-status`,
`/codex-result`, and `/codex-cancel` run the same script on demand, gate on or off.
