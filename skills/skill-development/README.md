# skill-development

Standards and a checker for building agent skills: naming, frontmatter, layout, progressive disclosure, README and INTENT files, temp paths, and bundled scripts. Works in any harness that reads `SKILL.md` folders.

## Use

Loads automatically when an agent creates, revises, renames, or reviews a skill. Examples:

- "Create a skill for our release process."
- "Review skills/my-skill against the skill standards."

Run the checker yourself on one skill or a folder of skills. `<skill-dir>` is the folder holding this skill's `SKILL.md`: wherever your harness installed it, or `skills/skill-development` in a library checkout.

```bash
python3 <skill-dir>/scripts/check_skill.py path/to/my-skill      # Windows: py -3
python3 <skill-dir>/scripts/check_skill.py path/to/skills --json
```

## Requirements

- Python 3.9+ for the checker (stdlib only). It accepts only a strict, unambiguous YAML subset in frontmatter. The guidance itself needs nothing.

## Results

The agent writes or edits only the target skill's folder. The checker reads files, prints findings, and exits `1` when it finds errors.
