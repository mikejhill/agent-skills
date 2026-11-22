# github-actions

Standards for GitHub Actions: CI that validates every change and shows its test results, tag-driven releases with automatic changelog promotion, Conventional Commits checks, caching, and workflow security.

## Use

Loads automatically when the agent creates, changes, or reviews files in `.github/workflows/`. Examples:

- "Set up CI and a release workflow for this Python project."
- "Why is this workflow so slow?"

## Requirements

- A GitHub repository. `gh` and `actionlint` help the agent verify action versions and lint workflows.

## Security and side effects

The agent writes workflow files only. Repository settings, secrets, tokens, and publishing credentials stay your decision; the `project-setup` skill covers how to configure them.
