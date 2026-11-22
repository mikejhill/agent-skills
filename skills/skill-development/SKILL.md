---
name: skill-development
description: >-
  Standards for creating, revising, renaming, or reviewing agent skills (SKILL.md
  folders): naming, frontmatter, layout, progressive disclosure, README and
  INTENT files, temp paths, and scripts. Use whenever you write or change a
  skill, or judge whether one is well built.
---

# Skill development

Build skills that trigger accurately, load little, and run in any harness. This file holds the rules every run needs. Load a reference only when the task reaches it.

## Workflow

1. **Intent first.** For a new skill, write `INTENT.md` from the user's ask before anything else, keeping their words for goals and requirements. For an existing skill, read `INTENT.md` first, then append a log entry after changing it. See [readme-and-intent.md](references/readme-and-intent.md).
2. **Name** the skill ([Naming](#naming)).
3. **Write frontmatter** ([Metadata](#metadata)). Write the description last, once the body is settled.
4. **Write `SKILL.md`**: the core path only. Move everything else into `references/` ([Progressive disclosure](#progressive-disclosure)).
5. **Add scripts or assets** only for work that is deterministic, fragile, or repeated ([Scripts](#scripts)).
6. **Write `README.md`** for users.
7. **Validate.** Run the checker, lint the Markdown, and test as described in [Checklist](#checklist).

Start from the templates in [assets/](assets/).

## Layout

```text
<skill-name>/
├── SKILL.md            # required: frontmatter + core instructions (for agents)
├── README.md           # required: short user-facing summary (for humans)
├── INTENT.md           # required: purpose, goals, requirements, log (for developers)
├── references/<topic>.md   # detail loaded on demand
├── scripts/<name>.py       # helpers the agent runs, from source
├── assets/                 # templates and static files to copy or fill in
├── tests/                  # tests for scripts/
└── agents/openai.yaml      # optional harness sidecar (see metadata.md)
```

- Create optional folders only when they hold something.
- Keep references one level deep. `SKILL.md` links to every file an agent may need, and those files link nowhere deeper.
- Use lowercase-kebab-case file names. Do not add other top-level docs, such as a CHANGELOG. The `INTENT.md` log covers history.
- Write paths relative to the skill folder. In commands, write `<skill-dir>` for the folder that contains `SKILL.md`, never the working directory.

## Naming

- Follow the spec: 1 to 64 characters, lowercase letters, digits, and single hyphens. The name must equal the folder name.
- Use a noun phrase for a skill that covers a subject: `python-development`, `project-setup`, `mermaid-diagrams`.
- Use verb-object only for a skill that performs one explicit action: `deploy-preview`, `rotate-keys`.
- Do not use gerunds: `managing-secrets` becomes `secret-management`, `writing-ai-instructions` became `skill-development`.
- Keep it to two or three words. Drop filler such as `helper`, `utils`, `tool`, or `my`.

## Metadata

Use only [Agent Skills spec](https://agentskills.io/specification) fields, plus the invocation extensions in [metadata.md](references/metadata.md).

| Field | Use |
| --- | --- |
| `name` | Required. See [Naming](#naming). |
| `description` | Required. See [Description](#description). |
| `compatibility` | Only for real environment needs: a runtime, a network service, or a harness restriction. |
| `license` | Only when the skill ships apart from a licensed repository. |
| `metadata` | Optional string map, such as `version`. Do not invent other top-level keys. |
| `allowed-tools` | Avoid. It is experimental and lists harness-specific tool names. |

Leave invocation flags unset by default, so both users and the model can invoke the skill. Restrict invocation only for the cases in [metadata.md](references/metadata.md).

## Description

The description is the only text an agent sees before it decides to load the skill. It must make that decision immediate.

- Write one to three sentences, aiming for 300 characters or fewer (the spec allows up to 1024).
- First, say what the skill does or covers, in the nouns users actually type.
- Then add "Use when …" with concrete triggers. Add "Not for …" only when a neighbouring skill could be confused with this one.
- Do not list every feature, market the skill, or repeat the name.
- Test it: from the name and description alone, an agent must answer yes or no correctly for five realistic requests, including two near-misses.

## Writing style

- Write for a capable agent. Include only what it would get wrong without being told. Cut background, motivation, and generic advice.
- Give a rule, and add the reason in a clause when the reason is not obvious. Use plain imperatives. Do not use all-caps MUST, banned-word lists, or personas.
- There is no mandatory section template. Use the sections the task needs, typically a purpose line, workflow, rules, a reference index, and a checklist.
- Prefer lists, tables, and one sharp example over prose or several examples.
- Do not restate what a formatter, linter, or script enforces. Name the tool instead.
- Keep it harness-neutral. Say "run", "read", or "edit", not harness tool names, slash commands, or harness paths. If a skill truly needs one harness, set `compatibility` and say so at the top of `README.md`.
- Aim for 200 lines or fewer in `SKILL.md`. The spec's hard limit is 500.

## Progressive disclosure

Keep in `SKILL.md` only what every run needs. Move everything else out, and link each file with a one-line "read when" trigger:

| Content | Goes in |
| --- | --- |
| Scenario-specific rules, deep or optional modes, edge cases | `references/<topic>.md` |
| Troubleshooting | `references/troubleshooting.md` |
| Long examples, lookup tables, API details | `references/<topic>.md` |
| Templates and files to copy | `assets/` |
| Deterministic or fragile procedures | `scripts/`. The agent runs these and does not read them; document the command and its output in `SKILL.md`. |

## Paths and temp files

| Purpose | Location |
| --- | --- |
| Scratch output tied to a workspace | `<workspace>/.tmp/<skill-name>/` (gitignored) |
| Temp output with no workspace, or for the user | `<system-temp>/agent-skills/<skill-name>/` |
| User configuration | `~/.config/agent-skills/<skill-name>/` |
| Cache and persistent state | `<user-cache>/agent-skills/<skill-name>/` |

Name ephemeral files `<kind>-<YYYYMMDD-HHMMSS>[-<slug>].<ext>` using local time, for example `report-20261122-175433-auth-flow.md`. Create them exclusively and never overwrite. Never write inside the skill folder at run time. For per-OS resolution and creation rules, read [paths.md](references/paths.md).

## Scripts

- Put scripts in `scripts/` and run them from source: `python3 "<skill-dir>/scripts/<name>.py"`. On Windows, use `py -3` or `python`.
- Default to stdlib-only Python 3.9 or later. Use Node.js (`.mjs`) only to wrap npm tooling. Use shell only for trivial wrappers, and provide both POSIX sh and PowerShell when Windows matters.
- Scripts are non-interactive. They provide `--help`, write results to stdout (JSON when an agent parses them), write diagnostics to stderr, and exit non-zero on failure.
- State OS limits in the script header and in `README.md`, and give the alternative for other OSes.

Read [scripts.md](references/scripts.md) before writing or changing a script.

## Checklist

- [ ] `python3 "<skill-dir>/scripts/check_skill.py" <target-skill-folder>` passes with no errors. It checks the name, frontmatter, sizes, required files, links, and gerunds.
- [ ] `npx markdownlint-cli2` passes for the skill's Markdown, if the repository uses it.
- [ ] Description test: five requests, including near-misses, are judged correctly from the description alone.
- [ ] One realistic task run follows the skill without loading references it did not need.
- [ ] `INTENT.md` still matches the skill. A new log entry records what changed and why.
- [ ] `README.md` states requirements, harness limits, side effects, and security notes, if any.

## References

- [metadata.md](references/metadata.md): read when setting invocation flags, `compatibility`, or harness sidecar files.
- [readme-and-intent.md](references/readme-and-intent.md): read when writing or updating `README.md` or `INTENT.md`.
- [paths.md](references/paths.md): read when a skill writes files outside the user's working files.
- [scripts.md](references/scripts.md): read when adding or changing a script or CLI.
- [other-features.md](references/other-features.md): read when the work is an instruction file, prompt, agent definition, or `AGENTS.md`, not a skill.
