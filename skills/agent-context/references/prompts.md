# Prompt files

A prompt file is a short task the user runs by name. It loads only when invoked.

## Format

```markdown
---
description: Summarise uncommitted changes as a draft commit message.
---

# Draft commit message

<What to do with the user's input, in a few steps.>
```

| Field | Use |
| --- | --- |
| `description` | What running it does, in one sentence. Users pick from this list. |

## Rules

- Prefer a user-only skill. Use a prompt only when the task fits on one screen and needs no scripts, references, or assets.
- Describe the expected input in prose, such as "the user may name a base branch". Argument placeholder syntax differs by harness, so avoid it in shared prompts.
- Write one task. A prompt that branches into modes is a skill.
- A prompt that only adapts another feature for one harness may name it; say so in the description and the intent file.

## Checklist

- [ ] Fits on one screen and does one task.
- [ ] Input is described in prose, not placeholder syntax.
- [ ] A `<name>.intent.md` sits beside the file.
