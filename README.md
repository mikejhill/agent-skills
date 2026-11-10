# Agent Skills

[![Markdown Lint](https://github.com/mikejhill/agent-skills/actions/workflows/markdown-lint.yml/badge.svg?branch=main)](https://github.com/mikejhill/agent-skills/actions/workflows/markdown-lint.yml)

Reusable skills, instructions, agents, prompts, and reference resources for AI coding assistants (Claude Code, GitHub Copilot, VS Code, Codex, and other harnesses that read `SKILL.md`-style folders).

The library is a [SkillSinc](https://github.com/mikejhill/skillsinc) source: SkillSinc converts and distributes each item into every configured harness.

## Structure

| Directory       | Contents                                                     |
| --------------- | ------------------------------------------------------------ |
| `skills/`       | One folder per skill, with `SKILL.md` and optional `references/`, `scripts/`, `assets/` |
| `instructions/` | Always-on or scoped instruction files (`<name>.instructions.md`) |
| `agents/`       | Custom agent definitions (`<name>.agent.md`)                 |
| `prompts/`      | Explicit, repeatable prompt files (`<name>.prompt.md`)       |
| `resources/`    | Reference guides loaded by other items                       |

## Usage

With SkillSinc, add this repository as a source in `~/.config/skillsinc/config.json`:

```jsonc
{
  "version": 1,
  "sources": {
    "public": { "path": "~/path/to/this/repo" },
  },
  // destinations and routes as usual
}
```

Then preview and apply:

```bash
skillsinc plan
skillsinc sync
```

Without SkillSinc, copy a skill folder into your harness's skills directory (for example `~/.claude/skills/` or `~/.agents/skills/`).

## License

[MIT](LICENSE)
