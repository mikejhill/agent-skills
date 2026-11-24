# Skills

Skills follow the [Agent Skills specification](https://agentskills.io/specification). Build them to trigger accurately, load little, and run in any harness.

## Workflow

1. Write `INTENT.md` (see the shared workflow).
2. Name the skill. The name must equal the folder name; the spec allows 1 to 64 characters.
3. Write frontmatter ([Metadata](#metadata)). Write the description last.
4. Write `SKILL.md`: the core path only. Move everything else into `references/` ([Progressive disclosure](#progressive-disclosure)).
5. Add scripts or assets only for work that is deterministic, fragile, or repeated ([Scripts](#scripts)).
6. Write `README.md` for users.
7. Validate with the [Checklist](#checklist).

Start from the templates in the skill's `assets/` folder.

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

## Metadata

Use only spec fields, plus the invocation extensions in [metadata.md](metadata.md).

| Field | Use |
| --- | --- |
| `name` | Required. |
| `description` | Required. |
| `compatibility` | Only for real environment needs: a runtime, a network service, or a harness restriction. |
| `license` | Only when the skill ships apart from a licensed repository. |
| `metadata` | Optional string map, such as `version`. Do not invent other top-level keys. |
| `allowed-tools` | Avoid. It is experimental and lists harness-specific tool names. |

Leave invocation flags unset by default, so both users and the model can invoke the skill. Restrict invocation only for the cases in [metadata.md](metadata.md). The spec allows a description up to 1024 characters; still aim for 300.

## Progressive disclosure

Keep in `SKILL.md` only what every run needs, and aim for 200 lines or fewer (the spec's hard limit is 500). Move everything else out, and link each file with a one-line "read when" trigger:

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
| Temp output with no workspace, or for the user | `<system-temp>/agent-skills/<skill-name>/` (Unix: `agent-skills-<uid>`) |
| Working directories with no workspace (clones, verification) | `<system-temp>/agent-skills/scratch/<kind>-<YYYYMMDD-HHMMSS>-<slug>/` (Unix: `agent-skills-<uid>`), removed when the task ends unless it holds unique work |
| User configuration | `~/.config/agent-skills/<skill-name>/` |
| Cache and persistent state | `<user-cache>/agent-skills/<skill-name>/` |

Name ephemeral files `<kind>-<YYYYMMDD-HHMMSS>[-<slug>].<ext>` using local time, for example `report-20261122-175433-auth-flow.md`. Create them exclusively and never overwrite. Never write inside the skill folder at run time. For per-OS resolution and creation rules, read [paths.md](paths.md).

## Scripts

- Put scripts in `scripts/` and run them from source: `python3 "<skill-dir>/scripts/<name>.py"`. On Windows, use `py -3` or `python`.
- Default to stdlib-only Python 3.9 or later. Use Node.js (`.mjs`) only to wrap npm tooling. Use shell only for trivial wrappers, and provide both POSIX sh and PowerShell when Windows matters.
- Scripts are non-interactive. They provide `--help`, write results to stdout (JSON when an agent parses them), write diagnostics to stderr, and exit non-zero on failure.
- State OS limits in the script header and in `README.md`, and give the alternative for other OSes.

Read [scripts.md](scripts.md) before writing or changing a script, and [cli.md](cli.md) for anything larger.

## Checklist

- [ ] `python3 "<skill-dir>/scripts/check_skill.py" <target-skill-folder>` passes with no errors. It checks the name, frontmatter, sizes, required files, links, gerunds, and references to sibling skills. `<skill-dir>` here is this standard's own folder.
- [ ] One realistic task run follows the skill without loading references it did not need.
- [ ] `README.md` states requirements, harness limits, side effects, and security notes, if any.
