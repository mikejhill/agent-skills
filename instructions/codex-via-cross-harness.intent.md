# Intent

Give Claude Code the openai-codex plugin's workflow (`/codex:review`,
`/codex:adversarial-review`, `/codex:rescue`, status, result, and cancel) on top of the
`cross-harness` skill, so the plugin can be disabled.

## Goals

1. Claude Code only. SkillSinc routes these items to the `claude` destination alone.
   Every other route excludes `instructions/codex-via-cross-harness` and
   `prompts/codex-*`.
2. Parity with the plugin's commands: `/codex-review`, `/codex-adversarial-review`,
   `/codex-rescue`, `/codex-status`, `/codex-result`, `/codex-cancel`.
3. Automatic review like the plugin's stop-time review gate: before finishing any
   task that changed code, run an adversarial Codex review of those changes, fix
   confirmed blocking findings, and stop after two rounds.
4. Verify Codex's output before acting on it or relaying it.

## Log

- 2026-11-19: [agent] Created at the user's request after the cross-harness skill
  merged. Covers the instructions file and six prompts. Routing exclusions were added
  to the local SkillSinc config on both machines.

- 2026-11-20: [agent] Rewrote the instructions as an automatic Codex review gate, per
  the user's correction: the plugin reviewed automatically, and a "use the skill instead
  of the plugin" rule adds nothing once the plugin is gone. The file name is kept so
  the SkillSinc route excludes stay valid.
