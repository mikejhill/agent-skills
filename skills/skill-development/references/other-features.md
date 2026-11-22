# Other agent features

The writing style, naming, and harness-neutral rules apply to every feature type. Pick the narrowest type that fits.

| Need | Type | Portable form |
| --- | --- | --- |
| On-demand capability, optionally with scripts or references | Skill | `skills/<name>/SKILL.md` |
| Rules for every task in one repository | Repository instructions | `AGENTS.md` at the repository root, with no frontmatter |
| Rules for most work, or for a file pattern, across repositories | Instruction file | `<name>.instructions.md` with `description` and an optional `applyTo` glob |
| A role with its own context, scope, or tool limits | Agent | `<name>.agent.md` with `name` and `description` |
| A short, explicit, user-run task | Prompt | `<name>.prompt.md` with `description` |
| A guaranteed action at a lifecycle event | Hook | Harness configuration. Not an instruction set. |

- Prefer a skill to a prompt. A user-only skill (see [metadata.md](metadata.md)) does the same job and can carry files.
- Prefer a skill to an instruction file unless the rule applies to most work. Always-on text costs context on every request, so keep instruction files under about 50 lines and make every line a rule.
- An agent definition states its role, its boundaries (what it must not do), and its output shape. Do not include a persona biography.
- Flat-file features keep their intent beside them as `<name>.intent.md`, in the [INTENT format](readme-and-intent.md#intentmd). They do not need a README.
