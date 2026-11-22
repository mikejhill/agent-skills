# project-setup

Principles for setting up or reviewing a repository: layout and root files, pull-request-based integration, required quality and security checks, deterministic tests, asynchronous mutation testing, and automated releases. A GitHub profile gives the concrete rulesets and release settings.

## Use

Loads automatically when the agent sets up a repository or designs its collaboration and release policies. Examples:

- "Set up this new repo properly."
- "Configure branch protection and releases for this project."

Language skills (such as `python-development`) and the `technical-documentation` and `github-actions` skills supply the details.

## Security and side effects

A proposed policy is not permission to change repository settings. The agent changes rulesets, permissions, secrets, or publishing settings only when you explicitly authorize it, and otherwise delivers the proposal and any readiness gaps.
