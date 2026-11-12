# Agent Skills

[![Markdown Lint](https://github.com/mikejhill/agent-skills/actions/workflows/markdown-lint.yml/badge.svg?branch=main)](https://github.com/mikejhill/agent-skills/actions/workflows/markdown-lint.yml)

Reusable skills, instructions, agents, prompts, and reference resources for AI coding assistants that follow the open [Agent Skills](https://agentskills.io) format and work across harnesses (Claude Code, Codex, and any other agent that reads `SKILL.md` folders).

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

With [SkillSinc](https://github.com/mikejhill/skillsinc) 0.5.0 or later, add this repository as a remote source in `~/.config/skillsinc/config.json`. SkillSinc keeps a cached checkout current (one `git ls-remote` per run) and keeps serving the last good copy if GitHub is unreachable:

```jsonc
{
  "version": 1,
  "sources": {
    "public": { "github": "mikejhill/agent-skills" },
  },
  // destinations and routes as usual
}
```

Pin a branch, tag, or commit with `"ref"`, and check the remote less often with `"refresh": "1h"`. See [remote sources](https://github.com/mikejhill/skillsinc/blob/main/docs/guides/configuration.md#remote-sources).

To sync a local clone instead (for example while editing it), use `"path": "~/path/to/agent-skills"`.

Then preview and apply:

```bash
skillsinc plan
skillsinc sync
skillsinc status   # remote check and error state for each source
```

Without SkillSinc, copy a skill folder into your harness's skills directory (for example `~/.claude/skills/` or `~/.agents/skills/`).

## License

[MIT](LICENSE)
