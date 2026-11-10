---
name: github-actions
description: "Use when creating, modifying, or refactoring GitHub Actions workflows for any project. Covers CI/CD pipeline design, GitOps-based releases with automated tagging and changelog generation, Conventional Commits enforcement, multi-environment matrix builds, performance optimization (caching, parallelism), test result presentation, and trusted action selection."
---

# GitHub Actions Skill

## Overview

This skill defines standards for GitHub Actions workflows across any
releasable project, regardless of language or framework. It produces CI
pipelines, release automation, and deployment workflows that are fast,
secure, and maintainable.

Three practices are **mandatory** and non-negotiable. Every workflow
produced by this skill enforces them.

## Required Practices

### 1. Conventional Commits

All commits MUST follow the
[Conventional Commits](https://www.conventionalcommits.org/v1.0.0/)
specification.

- Format: `type(scope): description` (scope is optional)
- Standard types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
  `test`, `build`, `ci`, `chore`, `revert`
- Breaking changes: append `!` after type/scope OR include
  `BREAKING CHANGE:` in the commit footer
- Version bump mapping: `fix` → PATCH, `feat` → MINOR,
  breaking change → MAJOR
- CI MUST validate commit messages on pull requests
- When using squash-merge, the PR title serves as the merge commit
  message and MUST follow conventional commit format

### 2. GitOps Tag-Driven Releases

Git tags are the **sole source of truth** for releases. Tags and
releases are tightly coupled.

- Version tags use the format `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`)
- Pre-release tags use a suffix: `v1.2.3-rc.1`, `v1.2.3-beta.1`
- Tags MUST be created exclusively by the release workflow — never
  pushed manually by developers
- Configure repository rulesets to protect tag patterns matching `v*`
  and restrict creation to the GitHub Actions actor
- One tag = one release = one set of published artifacts. This coupling
  is absolute.

### 3. Keep a Changelog

Every project MUST maintain a `CHANGELOG.md` file following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

- The `## [Unreleased]` section accumulates changes between releases
- During release, the workflow promotes `[Unreleased]` entries into a
  new versioned section with a date
- Use these categories: Added, Changed, Deprecated, Removed, Fixed,
  Security
- Developers write entries under `[Unreleased]`; the release workflow
  handles promotion. Never manually edit versioned sections.
- `CHANGELOG.md` is the human-curated record for developers. GitHub
  Release notes are the auto-generated record for consumers. Maintain
  both.

## Workflow Architecture

Every project MUST have at minimum these workflows:

| Workflow    | File           | Trigger                    | Purpose                              |
| ----------- | -------------- | -------------------------- | ------------------------------------ |
| **CI**      | `ci.yml`       | `push` and `pull_request`  | Validate code, run tests, check build |
| **Release** | `release.yml`  | `workflow_dispatch` manual | Version, tag, release, publish       |

Optional workflows:

| Workflow   | File          | Trigger                                | Purpose                            |
| ---------- | ------------- | -------------------------------------- | ---------------------------------- |
| **Deploy** | `deploy.yml`  | `release` event or `workflow_dispatch` | Promote a release to an environment |

### Separation of Concerns

- **CI** validates that code is correct and mergeable. It runs on every
  push and pull request. It NEVER publishes anything.
- **Release** ships code. It runs on demand via `workflow_dispatch`. It
  determines the version, creates the tag, builds artifacts, and
  publishes to registries.
- **Deploy** promotes a release to an environment. It is optional and
  only needed when deployment is separate from publishing.

Do not mix these responsibilities. CI does not release. Release does not
deploy (unless publishing IS the deployment).

## CI Workflow Design

### Scaffold

```yaml
name: CI

on:
  push:
    branches: [main]
    paths-ignore:
      - "*.md"
      - "docs/**"
      - "LICENSE"
  pull_request:
    branches: [main]
  merge_group:

permissions:
  contents: read
  checks: write
  pull-requests: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

Note: `paths-ignore` is set on `push` only — not on `pull_request` —
because skipping PR runs can block merge when required status checks
are configured.

### Jobs

Run these jobs in parallel (no `needs` unless a true dependency exists):

1. **Commit lint** (PR only) — Validate the PR title follows
   Conventional Commits
2. **Lint** — Static analysis, formatting, type checking
3. **Test** — Unit and integration tests (matrix for OS/versions if
   applicable)
4. **Build** — Verify artifacts can be produced (do NOT publish)

Optional: **Markdown lint**, **Security audit**

For branch protection stability, add a **ci-pass** aggregator job that
`needs` all other jobs and serves as the sole required status check.
This prevents matrix or job name changes from breaking protection
rules. See [Advanced Patterns](./references/advanced-patterns.md) for
the full pattern.

### Commit Message Validation

For squash-merge repositories (the most common strategy with
Conventional Commits), validate the PR title:

```yaml
commit-lint:
  if: github.event_name == 'pull_request'
  runs-on: ubuntu-latest
  permissions:
    pull-requests: read
  steps:
    - uses: amannn/action-semantic-pull-request@v6
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

For merge-commit or rebase-merge repositories, validate individual
commit messages using `commitlint`.

### PR vs Default Branch Deviations

| Concern                      | Pull Request              | Default Branch Push         |
| ---------------------------- | ------------------------- | --------------------------- |
| Commit message validation    | YES — validate PR title   | SKIP — validated at PR time |
| Full test matrix             | YES                       | YES                         |
| Build artifacts              | Verify build succeeds     | Verify build succeeds       |
| Code coverage                | Check and report          | Record and report           |
| Publish / deploy             | NEVER                     | NEVER                       |

See [CI Workflow Examples](./references/ci-workflow-examples.md) for
complete, production-ready templates for each ecosystem.

## Release Process

The release workflow uses `workflow_dispatch` so a human decides when to
release but automation handles the execution. This is the recommended
default; teams practicing continuous deployment may trigger releases
automatically on merge instead.

### Sequence

Execute these steps strictly in order. If any step fails, the workflow
halts — no partial releases.

1. **Checkout** — `fetch-depth: 0` for full git history
2. **Determine version** — Analyze conventional commits since the last
   tag; compute the next semantic version via dry-run
3. **Guard** — Abort if no releasable commits exist and `force-patch`
   is false
4. **Validate** — Run the full lint and test suite; MUST NOT proceed
   on failure
5. **Update CHANGELOG.md** — Promote `[Unreleased]` entries to a new
   versioned section
6. **Update version files** — Bump version in ecosystem manifests
   (`package.json`, `Cargo.toml`, `pyproject.toml`, etc.)
7. **Build** — Produce release artifacts
8. **Commit and tag** — Commit all changed files, create version tag,
   push both; use bot identity for the commit
9. **GitHub Release** — Create release with artifacts and generated
   release notes
10. **Publish** — Push to package registries (npm, PyPI, Maven Central,
    crates.io, NuGet, etc.)

See [Release Automation Reference](./references/release-automation.md)
for the complete workflow template with full YAML.

### Version Determination

| Tool                              | Best For                                          |
| --------------------------------- | ------------------------------------------------- |
| `semantic-release` (npm package)  | Node.js projects (rich plugin ecosystem)          |
| `go-semantic-release/action@v1`   | Language-agnostic projects (no runtime dependency) |
| Custom script                     | Full control over version logic                   |

Run in **dry-run mode** first. Use the computed version for CHANGELOG,
build, and tag steps.

### CHANGELOG and Release Automation

Use `sed` to insert a versioned section header below `[Unreleased]`.
Validate the CHANGELOG before and after mutation — confirm
`[Unreleased]` exists before `sed` and the new version header exists
after. Commit **all** changed files (CHANGELOG, manifests) — not just
`CHANGELOG.md`. Create the tag and push atomically. Use
`softprops/action-gh-release@v2` with `generate_release_notes: true`
for the GitHub Release.

See [Release Automation Reference](./references/release-automation.md)
for the complete workflow template with full YAML, ecosystem-specific
publishing, Docker layer caching, artifact attestation, and recovery
procedures.

### Branch Protection

The release workflow pushes commits and tags to the default branch.
Configure a branch protection bypass for `github-actions[bot]` or use
a GitHub App token. Document this in the repository's contributing
guide.

## Performance Optimization

### Runner Cost

GitHub-hosted runner billing: Linux 1×, Windows 2×, macOS 10×. Use Linux
for all jobs unless the project explicitly requires another OS.

### Caching

Use setup actions with built-in caching. Avoid manual `actions/cache`
unless no setup action covers your ecosystem.

| Ecosystem       | Setup Action                       | Caching                            |
| --------------- | ---------------------------------- | ---------------------------------- |
| Gradle          | `gradle/actions/setup-gradle@v4`   | Automatic                          |
| Maven           | `actions/setup-java@v4`            | `cache: maven`                     |
| Python (uv)     | `astral-sh/setup-uv@v8.1.0`        | Automatic                          |
| Python (pip)    | `actions/setup-python@v5`          | `cache: pip`                       |
| Node.js         | `actions/setup-node@v4`            | `cache: npm` (or `pnpm`, `yarn`)  |
| Go              | `actions/setup-go@v5`              | Automatic                          |
| Rust            | `Swatinem/rust-cache@v2`           | Automatic                          |
| .NET            | `actions/setup-dotnet@v4`          | Use `actions/cache` for NuGet      |

### Parallelism

- Jobs without `needs` run concurrently. Exploit this by splitting
  lint, test, and build into separate jobs.
- Add `needs` only when a job requires another's output.
- Use matrix strategies to parallelize across OS and runtime versions.

### Concurrency Control

- CI workflows: `cancel-in-progress: true` — newer pushes supersede
  stale runs.
- Release workflows: `cancel-in-progress: false` — never cancel an
  in-progress release.

### Conditional Execution

- Use `paths-ignore` to skip CI for documentation-only changes.
- Use `if` conditions for expensive steps that apply only to specific
  matrix entries.
- Collect code coverage on ONE matrix combination only (typically the
  latest runtime version on `ubuntu-latest`). Enforce thresholds with
  ecosystem tools (`--fail-under=80`, `jacocoTestCoverageVerification`,
  `c8 --check-coverage`).
- Use `if: always()` on reporting steps so they execute even when
  earlier steps fail.

### Timeouts

Set `timeout-minutes` on every job. Use 2–3× the expected duration.

## Multi-Environment Testing

Configure matrix strategies with `fail-fast: false` so all combinations
run to completion. Include only OS/version combinations the project
actually supports. Use `exclude` to skip unnecessary combinations and
`include` to attach flags (like `coverage: true`) to a single entry.
Name jobs descriptively:
`name: "Test (${{ matrix.os }}, v${{ matrix.version }})"`.

See [CI Workflow Examples](./references/ci-workflow-examples.md) for
matrix patterns in each ecosystem.

## Presentation

### Job Summaries

Write Markdown to `$GITHUB_STEP_SUMMARY` for rich output on the run
page. Use `if: always()` so summaries appear even on failure.

### Test Reporters

Always emit JUnit XML from test runs and render it into the run UI with a
dedicated reporter action. Two reporters are currently node24-native and
actively maintained:

- **`dorny/test-reporter@v3`** — creates a GitHub check with file-level
  annotations for failures. Good when you want a linkable check listed
  alongside other required checks.
- **`mikepenz/action-junit-report@v6`** — posts a detailed table into the
  run summary, adds check annotations, and supports passing a custom
  `check_name` per matrix leg. Good default when you want the results
  visible directly on the workflow run page.

Emit JUnit output from the test step and pass the XML to the reporter in
an `if: always()` step so failures still produce a report:

```yaml
- run: pytest --junitxml=junit.xml                              # or vitest, jest --reporters=jest-junit, gradle test, etc.
- name: Publish test report
  if: always()
  uses: mikepenz/action-junit-report@v6
  with:
    report_paths: junit.xml
    check_name: Tests (${{ matrix.os }} / py${{ matrix.python-version }})
    include_passed: true
    detailed_summary: true
    require_tests: true
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v7
  with:
    name: test-results-${{ matrix.os }}-py${{ matrix.python-version }}
    path: junit.xml
    if-no-files-found: ignore
```

When running a matrix, give each leg a unique `check_name` so results
don't overwrite each other. When running a `pull_request` from a fork,
note that `checks: write` is unavailable — fall back to
`$GITHUB_STEP_SUMMARY` markdown tables in that case.

**Do NOT omit test reporters.** A green workflow with no visible test
results is operationally equivalent to one that never ran tests.

### Build Scans (Gradle)

`gradle/actions/setup-gradle@v4` links build scans in workflow output
automatically. Add `--scan` to Gradle commands for public URLs.

### Annotations

Use `::error file=path,line=N::message` and `::warning::message`
workflow commands to surface issues inline on files.

## Security

### Permissions

Declare explicit permissions in every workflow. Never rely on repository
defaults. Start from zero and add only what each workflow requires.

- CI: `contents: read`, `checks: write`, `pull-requests: read`
- Release: `contents: write` (push tags, create releases)
- OIDC publishing: add `id-token: write`
- PR interactions: add `pull-requests: write`

### Script Injection Prevention

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
branch name, commit message, issue body) MUST be passed via `env:`,
never via `${{ }}` in `run:`.

### Fork Pull Request Security

Secrets are unavailable and `GITHUB_TOKEN` is read-only on
`pull_request` from forks. Do NOT use `pull_request_target` as a
workaround — it runs fork code with write permissions. See
[Advanced Patterns](./references/advanced-patterns.md) for the safe
two-workflow pattern.

### GITHUB_TOKEN Scope

`GITHUB_TOKEN` cannot trigger other workflows. If the release workflow
must trigger a deployment workflow, use a GitHub App installation token
or a fine-grained PAT with minimum necessary scopes.

### Authentication

- Prefer OIDC trusted publishing for registries that support it (PyPI,
  npm).
- Use GitHub environment protection rules with required reviewers for
  production deployments.
- Store third-party credentials as encrypted repository or environment
  secrets. Never log them.

### Action Pinning

Pin to major version tags for readability, or full commit SHAs for
maximum security in release workflows:

```yaml
uses: actions/checkout@v6                                              # Major tag
uses: actions/checkout@<full-commit-sha>                               # SHA pin
```

When SHA-pinning, look up the full commit hash for the tag on the
action's releases page. Dependabot automatically updates SHA pins.

Configure Dependabot to keep action versions current. See
[Release Automation Reference](./references/release-automation.md) for
the Dependabot configuration.

### Action Version Currency

Every workflow MUST use the latest major version of every action it
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

#### Verifying currency

Before committing a workflow, verify each `uses:` reference is on the
latest major version:

```bash
# Latest release of an action
gh api repos/{owner}/{repo}/releases/latest --jq .tag_name

# Node runtime declared by a published tag
curl -s https://raw.githubusercontent.com/{owner}/{repo}/{tag}/action.yml | grep "using:"
```

Every referenced action MUST declare `using: node24` (or a non-Node
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

#### Keeping currency

- Enable Dependabot for `github-actions` with `interval: weekly` and an
  `open-pull-requests-limit` that allows batched updates.
- Treat the resulting bump PRs as routine maintenance. Merge them after
  CI passes; they should rarely require manual intervention.
- During reviews, reject workflow changes that introduce `@v4` or older
  of any action with a newer major available, unless there is a
  documented, time-bounded blocker in a code comment.

## Trusted Actions

### Selection Criteria

Only use actions that meet ALL of these requirements:

- Published by GitHub (`actions/*`), a verified creator, or a
  recognized open-source organization
- Actively maintained — updated within the past 12 months
- Widely adopted — significant community usage and stars
- Open source — auditable code

### Curated List

| Purpose          | Action                                          |
| ---------------- | ----------------------------------------------- |
| Checkout         | `actions/checkout@v6`                           |
| Artifacts        | `actions/upload-artifact@v7`                    |
| Artifacts        | `actions/download-artifact@v8`                  |
| Attestation      | `actions/attest@v4`                             |
| Cache            | `actions/cache@v4`                              |
| Java             | `actions/setup-java@v4`                         |
| Node.js          | `actions/setup-node@v4`                         |
| Python           | `actions/setup-python@v5`                       |
| Go               | `actions/setup-go@v5`                           |
| .NET             | `actions/setup-dotnet@v4`                       |
| Gradle           | `gradle/actions/setup-gradle@v4`                |
| UV (Python)      | `astral-sh/setup-uv@v8.1.0`                     |
| Rust toolchain   | `dtolnay/rust-toolchain@stable`                 |
| Rust cache       | `Swatinem/rust-cache@v2`                        |
| Go lint          | `golangci/golangci-lint-action@v6`              |
| GitHub Release   | `softprops/action-gh-release@v3`                |
| Docker buildx    | `docker/setup-buildx-action@v3`                 |
| Docker build     | `docker/build-push-action@v6`                   |
| Docker login     | `docker/login-action@v3`                        |
| PyPI publish     | `pypa/gh-action-pypi-publish@release/v1`        |
| Test reporter    | `dorny/test-reporter@v3`                        |
| JUnit reporter   | `mikepenz/action-junit-report@v6`               |
| PR title lint    | `amannn/action-semantic-pull-request@v6`        |
| Semantic release | `go-semantic-release/action@v1`                 |
| Markdown lint    | `DavidAnson/markdownlint-cli2-action@v23`       |

The table above reflects current latest major versions. Action versions
move; see [Action Version Currency](#action-version-currency) for how to
keep them fresh on each repository.

**Avoid** actions with fewer than 100 stars, no updates in 12+ months,
unknown publishers, excessive permission requirements, or functionality
already covered by official `actions/*` actions.

## README Badges

Every project with GitHub Actions workflows MUST include status badges
in the README. Badges go immediately below the top-level heading
(`# Project Name`), before any description text.

### Required Badges

At minimum, include these badges:

| Badge             | Source                                                     |
| ----------------- | ---------------------------------------------------------- |
| **CI**            | GitHub Actions workflow badge for `ci.yml`                 |
| **Release**       | GitHub Actions workflow badge for `release.yml`            |
| **License**       | `img.shields.io/github/license/{owner}/{repo}`             |

### Optional Badges

Add these when applicable:

| Badge             | When to Include                              | Source                                              |
| ----------------- | -------------------------------------------- | --------------------------------------------------- |
| **Version**       | Published to a package registry              | `img.shields.io/pypi/v/{pkg}`, `npmjs.com`, etc.   |
| **Python version**| Python projects                              | `img.shields.io/pypi/pyversions/{pkg}`              |
| **Coverage**      | Coverage service configured                  | Codecov, Coveralls, or shields.io                   |
| **HACS**          | Home Assistant integrations                  | HACS badge from `hacs.xyz`                          |
| **Downloads**     | Published to a registry                      | `img.shields.io/pypi/dm/{pkg}`, etc.               |

### Format

Use Markdown image-link syntax with the badge image and a link to the
relevant page:

```markdown
[![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/ci.yml)
[![Release](https://github.com/{owner}/{repo}/actions/workflows/release.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/{owner}/{repo})](LICENSE)
```

Place all badges on consecutive lines (one per line) with a blank line
before and after the badge block.

## Anti-patterns

- **Manual tags** — Developers pushing tags bypasses the release
  workflow and violates GitOps
- **Tag-triggered releases** — Creates a chicken-and-egg problem; use
  `workflow_dispatch` instead
- **Publishing without validation** — The release workflow MUST run
  tests before publishing
- **Default permissions** — Repository defaults grant `write-all`;
  always declare explicit minimal permissions
- **Unbounded workflows** — Missing timeouts, concurrency groups, and
  path filters waste CI minutes
- **Untrusted actions** — Low-star, unmaintained actions are a
  supply-chain risk
- **Manual CHANGELOG edits for releases** — Automate the version
  section promotion in the release workflow
- **Mixing CI and release** — CI validates; release ships. Separate
  workflows, separate triggers, separate concerns.
- **Expression injection** — Using `${{ github.event.*.title }}` or
  similar user-controlled values directly in `run:` blocks
- **`pull_request_target` with checkout** — Runs fork code with write
  token; use the two-workflow pattern instead
- **`continue-on-error: true`** — Silently hides failures; use
  `if: always()` on reporting steps instead
- **`version: latest`** in lint actions — Breaks caching and
  reproducibility; pin to a specific version
- **Stale action majors** — Leaving `@v4` / `@v5` pinned after newer
  majors ship; causes Node.js runtime deprecation warnings and misses
  upstream fixes. See [Action Version Currency](#action-version-currency).
- **`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` / `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION`**
  — Masks deprecation warnings instead of fixing them; bump the action
  version instead.
- **Tests without a reporter** — Running `pytest` / `jest` / `go test`
  without emitting JUnit XML and publishing it via a test-reporter
  action makes failures invisible on the run page. See
  [Test Reporters](#test-reporters).

## Related Files

- `references/release-automation.md`: Complete release workflow template
  with CHANGELOG automation, ecosystem-specific publishing, deployment
  gating, Docker layer caching, artifact attestation, release failure
  recovery, and tag protection setup.
- `references/ci-workflow-examples.md`: Production-ready CI workflow
  templates for Gradle, Python, Node.js, Go, Rust, and .NET.
- `references/advanced-patterns.md`: Reusable workflows, composite
  actions, ci-pass aggregator job, GITHUB_TOKEN scope, fork PR
  handling, and debugging.

## Example

**Input:** "Create CI and release workflows for a Python project using
UV"

**Output:**

1. `.github/workflows/ci.yml` — Commit lint (PR only), ruff check +
   format, mypy, pytest matrix (ubuntu + windows, Python 3.12 + 3.13),
   markdownlint, concurrency control, path filters
2. `.github/workflows/release.yml` — `go-semantic-release` version
   determination, CHANGELOG promotion, `uv build`, tag push, GitHub
   Release, PyPI publish via OIDC
