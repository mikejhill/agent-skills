# Security

## Permissions

Declare explicit permissions in every workflow. Never rely on repository
defaults. Start from zero and add only what each workflow requires.

- CI: `contents: read`, `checks: write`, `pull-requests: read`
- Release: `contents: write` (push tags, create releases)
- OIDC publishing: add `id-token: write`
- PR interactions: add `pull-requests: write`

## Script Injection Prevention

**Never** interpolate event data directly in `run:` blocks. This is the
number-one Actions security vulnerability.

```yaml
# DANGEROUS — attacker-controlled PR title executes as shell code
run: echo "PR: ${{ github.event.pull_request.title }}"

# SAFE — pass through an environment variable
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: echo "PR: $PR_TITLE"
```

Any `github.event.*` value that originates from user input (PR title,
branch name, commit message, issue body) be passed via `env:`,
never via `${{ }}` in `run:`.

## Fork Pull Request Security

Secrets are unavailable and `GITHUB_TOKEN` is read-only on
`pull_request` from forks. Do NOT use `pull_request_target` as a
workaround — it runs fork code with write permissions. See
[Advanced Patterns](advanced-patterns.md) for the safe
two-workflow pattern.

## GITHUB_TOKEN Scope

`GITHUB_TOKEN` cannot trigger other workflows. If the release workflow
must trigger a deployment workflow, use a GitHub App installation token
or a fine-grained PAT with minimum necessary scopes.

## Authentication

- Prefer OIDC trusted publishing for registries that support it (PyPI,
  npm).
- Use GitHub environment protection rules with required reviewers for
  production deployments.
- Store third-party credentials as encrypted repository or environment
  secrets. Never log them.

## Action Pinning

Pin to major version tags for readability, or full commit SHAs for
maximum security in release workflows:

```yaml
uses: actions/checkout@v6                                              # Major tag
uses: actions/checkout@<full-commit-sha>                               # SHA pin
```

When SHA-pinning, look up the full commit hash for the tag on the
action's releases page. Dependabot automatically updates SHA pins.

Configure Dependabot to keep action versions current. See
[Release Automation Reference](release-automation.md) for
the Dependabot configuration.

## Action Version Currency

Every workflow use the latest major version of every action it
references. Stale versions cause three classes of problem observed in
practice:

1. **Runtime deprecation warnings.** GitHub periodically retires Node.js
   runtimes (Node 16 in 2023, Node 20 in 2026). Actions pinned to old
   majors still declare `using: node20` and generate deprecation
   annotations on every run until bumped.
2. **Missing bug fixes and performance improvements.** Major bumps of
   `actions/checkout`, `actions/upload-artifact`, `actions/setup-*`, and
   `astral-sh/setup-uv` routinely deliver faster caching, larger upload
   limits, and security patches.
3. **Incompatibility with newer runner images.** Older action majors
   occasionally break when Ubuntu / Windows / macOS runner images update
   their preinstalled toolchains.

**Do NOT use `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`, `FORCE_JAVASCRIPT_ACTIONS_TO_NODE20`,
or `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION` as a workaround.** These
environment variables force a mismatched Node runtime onto actions that
declare an older one. They silence the annotation but do not fix the
underlying maintenance debt, and they can introduce subtle runtime
incompatibilities. Bump the action version instead.

### Verifying currency

Before committing a workflow, verify each `uses:` reference is on the
latest major version:

```bash
# Latest release of an action
gh api repos/{owner}/{repo}/releases/latest --jq .tag_name

# Node runtime declared by a published tag
curl -s https://raw.githubusercontent.com/{owner}/{repo}/{tag}/action.yml | grep "using:"
```

Every referenced action declare `using: node24` (or a non-Node
runtime such as `docker` / `composite`) at the pinned tag. If a
dependency still ships `using: node20` at its latest tag, raise an
upstream issue and consider alternatives; do not mask the warning.

Not every publisher maintains a floating major tag. Before pinning to
`@vN`, confirm the tag exists:

```bash
gh api repos/{owner}/{repo}/tags --jq '.[].name' | head
```

If only `vN.M.P` tags are published (e.g. `astral-sh/setup-uv` at the
time of writing), pin to the specific patch version instead of `@vN`;
a non-existent floating tag causes an immediate workflow failure.

### Keeping currency

- Enable Dependabot for `github-actions` with `interval: weekly` and an
  `open-pull-requests-limit` that allows batched updates.
- Treat the resulting bump PRs as routine maintenance. Merge them after
  CI passes; they should rarely require manual intervention.
- During reviews, reject workflow changes that introduce `@v4` or older
  of any action with a newer major available, unless there is a
  documented, time-bounded blocker in a code comment.
