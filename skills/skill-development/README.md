# skill-development

Standards and a checker for building agent skills: naming, frontmatter, layout, progressive disclosure, README and INTENT files, temp paths, and bundled scripts. Works in any harness that reads `SKILL.md` folders.

## Use

Loads automatically when an agent creates, revises, renames, or reviews a skill. Examples:

- "Create a skill for our release process."
- "Review skills/browser-control against the skill standards."

Run the checker yourself on one skill or a whole folder of skills:

```bash
python3 skills/skill-development/scripts/check_skill.py skills/<name>   # Windows: py -3
python3 skills/skill-development/scripts/check_skill.py skills --json
```

## Requirements

- Python 3.9+ for the checker (stdlib only). The guidance itself needs nothing.

## Results

The agent writes or edits only the target skill's folder. The checker reads files, prints findings, and exits `1` when it finds errors.
