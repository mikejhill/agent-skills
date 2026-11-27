# Agent Skills

[![CI](https://github.com/mikejhill/agent-skills/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mikejhill/agent-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Reusable skills, instructions, agents, and prompts for AI coding assistants that follow the open [Agent Skills](https://agentskills.io) format and work across harnesses (Claude Code, Codex, and any other agent that reads `SKILL.md` folders).

The library is a [SkillSinc](https://github.com/mikejhill/skillsinc) source: SkillSinc converts and distributes each item into every configured harness.

## Structure

| Directory       | Contents                                                     |
| --------------- | ------------------------------------------------------------ |
| `skills/`       | One folder per skill: `SKILL.md`, `README.md`, `INTENT.md`, and optional `references/`, `scripts/`, `assets/` (standards: `skills/agent-context`) |
| `instructions/` | Always-on or scoped instruction files (`<name>.instructions.md`) |
| `agents/`       | Custom agent definitions (`<name>.agent.md`)                 |
| `prompts/`      | Explicit, repeatable prompt files (`<name>.prompt.md`)       |
| `harnesses/<harness>/` | Items for one harness only, in the same kind folders (`skills/`, `instructions/`, `agents/`, `prompts/`); see [Harness-specific items](#harness-specific-items) |

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

### Harness-specific items

Everything at the root is harness-neutral and goes to every harness. An item that only works in, or only applies to, one harness lives under `harnesses/<harness>/` instead, using the same kind folders as the root. `<harness>` is the SkillSinc profile name: `claude`, `codex`, `copilot`, or `vscode`.

| Folder | Holds today |
| --- | --- |
| `harnesses/claude/` | `instructions/claude-file-links`, `instructions/codex-via-cross-harness`, `prompts/codex-*` (the Codex review gate and commands run from Claude Code) |
| `harnesses/codex/` | `instructions/codex-attribution` |

SkillSinc reads only the kind folders at a source's root, so the main source never sees `harnesses/`. Add one source per harness folder and route it to that harness's destination alone. Adding or removing a harness-specific item then needs no configuration change:

```jsonc
{
  "sources": {
    "public": { "github": "mikejhill/agent-skills" },
    "public-claude": { "github": "mikejhill/agent-skills", "subdirectory": "harnesses/claude" },
    "public-codex": { "github": "mikejhill/agent-skills", "subdirectory": "harnesses/codex" },
  },
  "routes": [
    { "sources": ["public"], "destinations": ["claude", "codex", "copilot", "vscode", "agents"], "allow_lossy": true },
    { "sources": ["public-claude"], "destinations": ["claude"], "allow_lossy": true },
    { "sources": ["public-codex"], "destinations": ["codex"], "allow_lossy": true },
  ],
}
```

With a local clone, use `"path": "~/path/to/agent-skills/harnesses/claude"`. Add a harness source only once its folder exists: a missing folder fails the source.

Limits:

- Skills for Codex, Copilot CLI, and VS Code all load from `~/.agents/skills`, so a skill cannot be isolated to one of them. VS Code also reads `~/.claude/skills` unless its `chat.agentSkillsLocations` setting turns that off. Prefer a harness-neutral skill and state any harness limit in its README.
- An item for several harnesses but not all stays at the root and is excluded per route.
- Harness sidecar files inside a neutral skill, such as `agents/openai.yaml`, stay with the skill; they are ignored by other harnesses.

Without SkillSinc, copy a skill folder into your harness's skills directory (for example `~/.claude/skills/` or `~/.agents/skills/`).

## Checks

[CI](.github/workflows/ci.yml) runs on every pull request and on `main`. The `ci-pass` job aggregates the others; it and `pr-title` ([pr-title.yml](.github/workflows/pr-title.yml)) are the required checks for merging.

| Job | What it checks |
| --- | --- |
| Skill format | Every skill against the [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) reference validator and the `agent-context` checker |
| Code lint | Python (ruff), shell (shellcheck), PowerShell (PSScriptAnalyzer), YAML (yamllint), and workflows (actionlint) |
| Markdown lint | markdownlint-cli2 with [.markdownlint-cli2.jsonc](.markdownlint-cli2.jsonc) |
| Tests | Skill unit tests and script smoke tests on Linux (Python 3.9 and latest), Windows, and macOS |
| Language coverage | Fails when a skill adds a script in a language no job lints or tests (for example Go or TypeScript); add a job for it first |
| PR title | Conventional Commits |

Run them locally from the repository root (needs Python 3.11+, Node.js, and PowerShell 7):

```bash
pip install -r .github/ci/requirements.txt -r .github/ci/requirements-test.txt
python .github/ci/skills_ref_check.py
python skills/agent-context/scripts/check_skill.py skills
.github/ci/lint.sh   # ruff, shellcheck, PSScriptAnalyzer, yamllint, actionlint (same as CI)
npx markdownlint-cli2
python -m pytest
```

## License

[MIT](LICENSE)
