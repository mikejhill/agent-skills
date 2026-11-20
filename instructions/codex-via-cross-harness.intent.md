# Intent

Give Claude Code the openai-codex plugin's workflow on top of the `cross-harness`
skill, including its automatic review gate, so the plugin can be removed.

## Goals

1. Claude automatically gets a Codex review of its changes before finishing a turn
   that changed repository files, without the user asking, like the plugin's
   stop-time review gate.
2. Claude Code only. SkillSinc routes these items to the `claude` destination alone.
   Every other route excludes `instructions/codex-via-cross-harness` and
   `prompts/codex-*`.
3. The gate stays bounded: at most two review rounds per turn, and nothing leaks
   processes or loops without limit.
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
