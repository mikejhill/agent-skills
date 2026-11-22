# README.md and INTENT.md

Agents running a skill read neither file. Keep them out of `SKILL.md` links and out of any frontmatter list of files.

| File | Reader | Job |
| --- | --- | --- |
| `README.md` | Users skimming | What the skill does, how to use it, what to watch out for |
| `INTENT.md` | Skill developers, human or agent | Why the skill exists and what it must achieve, in enough detail to rebuild it |

## README.md

Start from [README.template.md](../assets/README.template.md). Expect a cursory glance, so aim for under 40 lines.

- Open with one sentence on what the skill does. If it is limited to certain harnesses or OSes, say so in the next line.
- **Use:** how it is invoked (automatically, or by the user only) and one or two example requests.
- **Requirements:** runtimes, CLIs, accounts, network access. Omit if none.
- **Results:** what the user gets and where files land.
- **Security and side effects:** credentials touched, data sent, anything written outside the workspace. Omit if none.
- Do not repeat the skill's instructions.

## INTENT.md

Start from [INTENT.template.md](../assets/INTENT.template.md). It must be possible to rebuild the skill from this file alone.

| Section | Content |
| --- | --- |
| Purpose line | One sentence: what the skill does and why it exists. |
| `## Goals` | Ranked desired outcomes. A higher goal wins a conflict. Each must be testable by an observer. |
| `## Requirements` | Constraints and specifics the operator asked for: required behaviour, exclusions, environments, conventions. Keep the operator's wording wherever possible. |
| `## Log` | Append-only, one dated line per decision or change. |

- Agents often write this file, but it must read as the operator's asks. Do not add goals or requirements the operator did not state or approve. Record agent inferences as `[agent]` log entries instead.
- Log entries: an operator decision is `- YYYY-MM-DD: text`, and an agent change or observation is `- YYYY-MM-DD: [agent] text`.
- When iterating, append to the log and do not edit existing goals, requirements, or entries unless the operator asks. When the operator changes a goal, edit it and log the change.
- When creating a skill from an existing `INTENT.md`, treat goals and requirements as binding, and treat the log as context.
