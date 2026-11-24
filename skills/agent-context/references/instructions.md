# Instruction files

An instruction file is loaded into every request it matches, whether or not the task needs it. Every line costs context on every one of those requests.

## Format

```markdown
---
name: Short Title
description: One sentence on what these rules govern.
applyTo: "**/*.py,**/pyproject.toml"
---

# Short Title

- Rule.
- Rule, with the reason in a clause when it is not obvious.
```

| Field | Use |
| --- | --- |
| `name` | Short human-readable title. |
| `description` | One sentence on what the rules govern. Some harnesses use it to decide relevance, so write it like a skill description. |
| `applyTo` | Comma-separated globs for the files these rules cover. `"**"` means every request; use it only for rules that truly apply to all work. |

## Rules

- Keep it under about 50 lines, and make every line a rule. Move procedures, examples, and reference material into a skill.
- Scope with `applyTo` before reaching for `"**"`. A narrow glob keeps the rules out of unrelated work.
- One subject per file. Split a file that mixes, say, commit conventions and temp paths, so each can be routed or dropped alone.
- Write rules that hold everywhere the file is installed. Machine-specific paths, account names, and private hosts belong in a private library or the user's own config.
- A rule for only one harness goes in its own file, named for that harness, and says so in its description. Route it only to that harness with the distribution tool's config.
- Do not restate repository-specific facts here; they belong in that repository's `AGENTS.md`.

## Checklist

- [ ] Under about 50 lines, every line a rule.
- [ ] `applyTo` is as narrow as the rules allow.
- [ ] A `<name>.intent.md` sits beside the file.
