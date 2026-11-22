---
name: gitignore-standards
description: >-
  Standard layout for .gitignore files: the base template, unaltered
  github/gitignore templates, then one project-specific section. Use when
  creating, updating, reviewing, or refactoring any .gitignore.
---

# Gitignore standards

Every `.gitignore` has three section groups, in this order, separated by one blank line:

```gitignore
### Base Template
<assets/base.gitignore, copied unaltered>

### <Name> Template
<a github/gitignore template, copied unaltered>

### Project-Specific Rules
<everything this project adds or overrides>
```

## Rules

- Copy [base.gitignore](assets/base.gitignore) verbatim, including its `### Base Template` heading.
- Add one section per template from [github/gitignore](https://github.com/github/gitignore) (for example `Python`, `Node`, `Terraform`), headed `### <Name> Template`. Fetch the current upstream text and do not edit it. Omit templates the project does not need.
- Put every custom pattern, override, and re-include (`!pattern`) in the single `### Project-Specific Rules` section, last. Comment non-obvious patterns.
- Add no other section types.
- When updating an existing file, move stray custom lines into Project-Specific Rules, and replace edited template copies with the upstream text.

## Checklist

- [ ] Order: Base, then templates, then Project-Specific Rules.
- [ ] Base and template sections match their sources exactly.
- [ ] Exactly one Project-Specific Rules section.
- [ ] One blank line between sections.
- [ ] `git status --ignored` shows nothing unexpected ignored or tracked.
