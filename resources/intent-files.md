# Intent Files

Intent files record the operator's goals, priorities, and decision history
for an agent feature (skill, instructions, agent, prompt, or hook). They serve as governance documents for feature
creation, regeneration, and ongoing maintenance.

## Purpose

When agents create or iterate on features, the operator's original goals and
accumulated decisions are lost between sessions. Intent files preserve this
context so that:

- A feature can be regenerated from goals alone.
- Iterative enhancements are recorded as they happen.
- Feature quality can be judged against stated goals.
- New agents inherit the operator's priorities without re-explanation.

## Audience

Intent files are for:

- **Human operators** reviewing or updating their features.
- **Agents creating or maintaining features** (e.g., via the
  `writing-ai-instructions` skill or refinement workflows).

Intent files are NOT for agents consuming the feature. An agent using the
python-development skill does not need the python-development intent file.

## File Placement

| Feature type       | Intent file                           |
| ------------------ | ------------------------------------- |
| Agent skills       | `<skill-directory>/INTENT.md`         |
| Instructions files | `<instructions-dir>/<name>.intent.md` |
| Prompt files       | `<prompts-dir>/<name>.intent.md`      |
| Custom agents      | `<agents-dir>/<name>.intent.md`       |
| Agent hooks        | `<hooks-dir>/<name>.intent.md`        |

Skills use `INTENT.md` (uppercase) because they have a dedicated directory.
Flat-file features use `<name>.intent.md` as a companion file in the same
directory as the feature. Reference resources do not use intent files — they
serve a parent feature whose intent file covers them.

Intent files MUST NOT be included in a skill's frontmatter `references` list.
They are not loaded when the feature is invoked.

## Format

````markdown
# Intent

One-line statement of what this feature does and why it exists.

## Goals

1. Most important goal — wins when goals conflict
2. Second priority goal
3. Additional goals as needed

## Log

- YYYY-MM-DD: Description of a decision, change, or observation
````

### Sections

#### Purpose line

A single sentence after the `# Intent` heading. States the feature's reason
for existence. This anchors all other content — goals and log entries are
interpreted relative to this purpose.

#### Goals

Numbered list ordered by priority. When goals conflict during feature
development, higher-ranked goals win. Goals MUST be:

- **Declarative** — state what, not how
- **Testable** — an observer can judge whether the feature meets the goal
- **Stable** — goals change infrequently; implementation details change often

Aim for 3–7 goals. Fewer than 3 suggests under-specification. More than 7
suggests the feature's scope is too broad or goals are too granular.

#### Log

Append-only chronological record. Each entry is a single line with a date
prefix. Two categories:

- **Operator entries** — Decisions made by the human operator. No prefix
  beyond the date.
- **Agent entries** — Observations or changes recorded by an agent during
  feature iteration. Prefixed with `[agent]` after the date.

The distinction matters: operator entries are authoritative decisions; agent
entries are informational records the operator may later promote, revise,
or remove.

## Agent Behavior

### Creating a feature from an intent file

1. Read the intent file.
2. Treat goals as binding requirements ordered by priority.
3. Treat log entries as context — they inform implementation but do not
   override goals.
4. Create the feature. Do NOT modify the intent file during initial creation.

### Iterating on an existing feature

1. Read the intent file to understand goals and history.
2. Make the requested changes to the feature.
3. Append a log entry summarizing what changed and why. Use the `[agent]`
   prefix.
4. Do NOT modify existing goals or log entries unless the operator explicitly
   asks.

### Updating goals

When the operator asks to change goals:

1. Edit the Goals section as directed.
2. Append a log entry noting the goal change.
