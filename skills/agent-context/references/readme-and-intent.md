# README and intent files

Agents running a feature read neither file. Keep them out of a skill's `SKILL.md` links and out of any frontmatter list of files.

| File | Reader | Job |
| --- | --- | --- |
| README | Users skimming | What the feature does, how to use it, what to watch out for |
| Intent file | Feature developers, human or agent | Why the feature exists and what it must achieve, in enough detail to rebuild it |

## Placement

| Feature | README | Intent file |
| --- | --- | --- |
| Skill | `<skill>/README.md` | `<skill>/INTENT.md` |
| Instruction file | none | `<name>.intent.md` beside `<name>.instructions.md` |
| Agent | none | `<name>.intent.md` beside `<name>.agent.md` |
| Prompt | none | `<name>.intent.md` beside `<name>.prompt.md` |
| Hook | none | `<name>.intent.md` beside the hook script or config |
| `AGENTS.md`, `CLAUDE.md` | none | none; the repository's history covers them |

Reference files inside a skill have no intent file; the skill's `INTENT.md` covers them.

## README.md

Start from the skill's `assets/README.template.md`. Expect a cursory glance, so aim for under 40 lines.

- Open with one sentence on what the skill does. If it is limited to certain harnesses or OSes, say so in the next line.
- **Use:** how it is invoked (automatically, or by the user only) and one or two example requests.
- **Requirements:** runtimes, CLIs, accounts, network access. Omit if none.
- **Results:** what the user gets and where files land.
- **Security and side effects:** credentials touched, data sent, anything written outside the workspace. Omit if none.
- Do not repeat the skill's instructions.

## Intent file

Start from `assets/INTENT.template.md`. It must be possible to rebuild the feature from this file alone.

| Section | Content |
| --- | --- |
| Purpose line | One sentence after `# Intent`: what the feature does and why it exists. |
| `## Goals` | Ranked desired outcomes, usually 3 to 7. A higher goal wins a conflict. Each must be testable by an observer. |
| `## Requirements` | Constraints and specifics the operator asked for: required behaviour, exclusions, environments, conventions. Keep the operator's wording wherever possible. |
| `## Log` | Append-only, one dated line per decision or change. |

- Agents often write this file, but it must read as the operator's asks. Do not add goals or requirements the operator did not state or approve. Record agent inferences as `[agent]` log entries instead.
- Log entries: an operator decision is `- YYYY-MM-DD: text`, and an agent change or observation is `- YYYY-MM-DD: [agent] text`.
- When iterating, append to the log and do not edit existing goals, requirements, or entries unless the operator asks. When the operator changes a goal, edit it and log the change.
- When creating a feature from an existing intent file, treat goals and requirements as binding, treat the log as context, and do not edit the file during creation.
