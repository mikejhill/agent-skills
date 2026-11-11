---
name: skillsinc
description: Create and maintain reusable skills, instructions, agents, and prompts in the user's SkillSinc library and distribute them across configured AI harnesses.
---

# SkillSinc library workflow

Maintain shared guidance at its source and distribute it using SkillSinc's
existing plan and sync workflow.

## Locate the source

Run `skillsinc --version` and inspect `skillsinc plan --help`. Read the active
configuration named there (normally `~/.config/skillsinc/config.json`, with
`XDG_CONFIG_HOME` honored). Resolve the selected source's `path` and routes.
Do not assume the tool repository is the user's library. Do not replace an
existing configuration with `init --force`.

SkillSinc reads local directories. Git history belongs to the library's local
repository; SkillSinc does not clone, pull, commit, or push it. Check the library's
Git status and applicable instructions before editing. If it is not versioned,
report that gap; do not claim that a local file has Git history.

## Author once

- Put skills in `skills/<name>/SKILL.md` with `name` and `description` frontmatter.
- Put shared instructions in `instructions/<name>.instructions.md`. Use
  `applyTo: "**"` for guidance intended to apply to all tasks.
- Put agents in `agents/<name>.agent.md` and prompts in
  `prompts/<name>.prompt.md` when requested.
- Edit canonical sources, including this skill and its companion instruction.
  Never patch managed destination copies as the durable fix.
- Keep project-specific instructions in their project. Keep private content
  local; remote publication requires authorization. Do not add credentials to
  library content or stage unrelated files.

## Preview and distribute

Run `skillsinc plan` using the active configuration. Inspect every create,
update, delete, ownership conflict, and conversion loss, including changes
unrelated to the current edit. Stop if the plan includes unapproved changes.
Do not use `--adopt` or enable lossy conversion without reviewing its effect.

When distribution is authorized, run `skillsinc sync` with the same configuration
and destination selection, then run `skillsinc plan` again to verify convergence.
For manual-only use, leave the preview ready and state that sync is pending.
Do not install a scheduler or push a Git remote as part of editing guidance.

Instructions render into Claude rules, Copilot instructions, VS Code instructions,
and a managed block in Codex `AGENTS.md`. Codex discovers skills through the
`agents` profile's `~/.agents/skills`; the `codex` profile does not copy skills.
Run `skillsinc profiles` to check installed-version support for other kinds.

Review the source Git diff and stage only intended guidance files. Commit locally
within the user's authorization, preserving unrelated work. Report source paths,
Git status, distribution results, and blockers separately. A successful sync is
not evidence of a Git commit or proof that an already-running harness reloaded.

Explicit user instructions and repository scope take precedence over defaults
in this skill; preserve private content and existing ownership throughout.
