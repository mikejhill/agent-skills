# agent-context

Standards for writing agent context: skills, instruction files, agent definitions, prompt files, `AGENTS.md`, and `CLAUDE.md`. One shared writing style, plus a reference per feature type and a checker for skills. Works in any harness that reads `SKILL.md` folders.

## Use

Loads automatically when an agent creates, revises, renames, or reviews any of these. Examples:

- "Create a skill for our release process."
- "Write an AGENTS.md for this repository."
- "Review instructions/git-conventions.instructions.md against the standards."

Run the skill checker yourself on one skill or a folder of skills. `<skill-dir>` is the folder holding this skill's `SKILL.md`: wherever your harness installed it, or `skills/agent-context` in a library checkout.

```bash
python3 <skill-dir>/scripts/check_skill.py path/to/my-skill      # Windows: py -3
python3 <skill-dir>/scripts/check_skill.py path/to/skills --json
```

## Requirements

- Python 3.9+ for the checker (stdlib only). It accepts only a strict, unambiguous YAML subset in frontmatter. The guidance itself needs nothing.
- The checker covers skills only. Other feature types are checked against their reference's checklist.

## Results

The agent writes or edits only the target feature and its intent file. The checker reads files, prints findings, and exits `1` when it finds errors.
