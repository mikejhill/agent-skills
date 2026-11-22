# gitignore-standards

Keeps every `.gitignore` in one predictable layout: a shared base template, unmodified templates from [github/gitignore](https://github.com/github/gitignore), and one section for project-specific rules.

## Use

Loads automatically for any `.gitignore` work. Example: "Add a .gitignore for this Python project."

The base template is `assets/base.gitignore`. It ignores `.tmp/` (agent scratch space), `.env` files, OS and editor files, and common build outputs.

## Requirements

- Network access to fetch github/gitignore templates. Without it, the agent says which templates it could not fetch.
