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
3. Natural-language requests ("have Codex review this") use the skill, never the
   old plugin.
4. Use Codex only when asked. Verify its output before relaying it.

## Log

- 2026-11-19: [agent] Created at the user's request after the cross-harness skill
  merged. Covers the instructions file and six prompts. Routing exclusions were added
  to the local SkillSinc config on both machines.
