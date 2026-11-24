# Agent definitions

An agent definition describes a role another agent delegates to. Whether the delegate sees the caller's conversation depends on the harness and how it is launched, so write the definition to work from the caller's brief alone, and never rely on isolation to keep information from it.

## Format

```markdown
---
name: release-notes
description: Drafts release notes from merged pull requests since a tag. Use when preparing a release.
---

# Release notes

<Role in one sentence: the outcome this agent produces.>

## Scope

- In: <what it may read, change, or run>
- Out: <what it must not touch or decide>

## Process

1. <step>

## Output

<The exact shape returned to the caller: sections, fields, or a file path.>
```

| Field | Use |
| --- | --- |
| `name` | The feature name. |
| `description` | What the agent does and when to delegate to it. The caller chooses from this alone, so apply the description test. |

Leave out harness-specific fields such as tool lists, model names, or colours. When a harness needs one, add it through the distribution tool or a harness-scoped copy, and record why in the intent file.

## Rules

- State the role, the boundaries, and the output shape. These three are what a delegate gets wrong most often.
- Make boundaries concrete: name the actions it must not take, such as pushing, deleting, or editing outside a path, and what it does instead (report, ask).
- Define an output the caller can use without rereading the delegate's work: findings with file and line, a verdict, or a file path. Say what to return when there is nothing to report.
- Do not write a persona or biography. "You are a senior engineer with 20 years …" adds tokens and nothing else.
- Prefer a skill when no separate context is needed. An agent earns its place by isolating context, running in parallel, or limiting what it can do.
- Keep the body under about 150 lines. Move long checklists or rubrics into a skill the agent can load, referred to by capability.

## Checklist

- [ ] Role, boundaries, and output shape are explicit.
- [ ] Runs correctly from a one-line brief, with no conversation history.
- [ ] No persona, and no harness-specific fields without a recorded reason.
- [ ] A `<name>.intent.md` sits beside the file.
