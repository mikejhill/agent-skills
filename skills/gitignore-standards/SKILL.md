---
name: gitignore-standards
description: Use for all .gitignore tasks. Apply these standards whenever creating, updating, reviewing, or refactoring .gitignore content.
---

# GitIgnore Standards Skill

## Objective

Produce and maintain `.gitignore` content with exactly three section groups in this order:

1. Base template reference
2. One or more unaltered GitHub gitignore templates
3. One project-specific rules section

## Base .gitignore Template Reference

Use the canonical base template file at [references/base-gitignore-template.gitignore](./references/base-gitignore-template.gitignore).

## Required Structure

Use this exact section order and heading format:

```gitignore
### Base Template
<unaltered content from ./references/base-gitignore-template.gitignore>

### <Name> Template
<unaltered content from github/gitignore>

### <Name> Template
<unaltered content from github/gitignore>

### Project-Specific Rules
<custom project patterns>
```

## Complete Example (Trimmed)

This is a concise end-to-end example with multiple template sections and short content excerpts:

```gitignore
### Base Template
# Agent and Developer Temporary Files
.tmp/

### Python Template
__pycache__/
*.py[cod]
.venv/

### Terraform Template
.terraform/
*.tfstate
*.tfstate.*

### Project-Specific Rules
# Repository-specific additions
coverage-final/
terraform.local.tfvars
!.env.production.template
```

## Rules

- Apply this skill to every `.gitignore` task: create, update, review, and refactor.
- The base template section MUST copy unaltered content from [Base .gitignore Template](./references/base-gitignore-template.gitignore) into the generated output.
- Each imported GitHub template section MUST start with exactly one heading line in this format: `### <Name> Template`.
- Imported GitHub templates MUST remain unaltered from their original source text.
- There MUST be exactly one `### Project-Specific Rules` section.
- Put all project-specific additions or overrides in `### Project-Specific Rules`, including re-adding any desired patterns ignored by earlier templates.
- Separate sections with exactly one blank line.
- Do not add extra section types.

## Validation Checklist

- Order is Base -> GitHub templates -> Project-Specific Rules.
- Base template content is copied unaltered from [references/base-gitignore-template.gitignore](./references/base-gitignore-template.gitignore) and embedded inline.
- Every GitHub template has a `### <Name> Template` heading.
- GitHub template text is unmodified.
- Only one `### Project-Specific Rules` section exists.
- Exactly one blank line separates adjacent sections.
