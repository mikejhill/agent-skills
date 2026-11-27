# Intent

Give Claude Code the openai-codex plugin's workflow on top of the `cross-harness`
skill, including its automatic review gate, so the plugin can be removed.

## Goals

1. Match the plugin's stop-time review gate. It is opt-in per repository and off by
   default. Where it is on, Claude gets an adversarial Codex review of each turn's
   direct code edits before finishing that turn.
2. Claude Code only. The instruction and prompts live under `harnesses/claude/`,
   which SkillSinc routes to the `claude` destination alone.
3. The gate stays bounded: at most two review rounds per turn. The plugin loops until
   Codex allows the stop. Nothing leaks processes.
4. Codex's output is verified before it's relayed. It's never presented as the
   verdict.
5. Parity with the plugin's commands: `/codex-review`, `/codex-adversarial-review`,
   `/codex-rescue`, `/codex-status`, `/codex-result`, `/codex-cancel`.

## Log

- 2026-11-19: [agent] Created at the user's request after the cross-harness skill
  merged. Covers the instructions file and six prompts. Routing exclusions were added
  to the local SkillSinc config on both machines.
- 2026-11-20: The user clarified that the instruction must make Claude run Codex
  reviews automatically, like the plugin's review gate. A rule that only says "use
  the skill, not the plugin" adds nothing once the plugin is gone. Goals were
  rewritten: "use Codex only when asked" was replaced by the automatic gate.
- 2026-11-20: [agent] Rewrote the instructions file as a review gate. It runs after
  any turn that changes repository files, before completion, commit, or merge. It
  verifies and fixes confirmed findings, stops after two rounds, and is skipped for
  read-only turns, user opt-out, and sessions that Codex started.
- 2026-11-20: The user questioned whether the plugin really reviewed every editing
  turn. [agent] Checked upstream 1.0.6:
  - `hooks/hooks.json` registers a `Stop` hook, `stop-review-gate-hook.mjs`. It returns
    at once unless `stopReviewGate` is set in the workspace's state.
  - `stopReviewGate` defaults to false (`lib/state.mjs`). `/codex:setup
    --enable-review-gate` sets it, per workspace root.
  - When the gate is on, the hook runs a read-only Codex task on every stop, using
    `prompts/stop-review-gate.md`. Codex answers ALLOW right away unless that turn made
    direct edits, and BLOCK stops Claude from finishing, with no round limit.
  - The README warns that it can loop and drain usage limits.

  The gate now follows that design. It is opt-in per repository, through `git config
  --local cross-harness.reviewGate true`, and off by default. It reviews only this
  turn's edits, adversarially, and stops after two rounds.
- 2026-11-27: [agent] Moved the instruction and the six prompts to
  `harnesses/claude/` under the harness-folder convention, replacing the per-item
  route excludes.
