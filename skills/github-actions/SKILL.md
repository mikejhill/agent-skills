---
name: github-actions
description: >-
  Standards for GitHub Actions workflows: CI design, tag-driven releases with
  changelog automation, Conventional Commits checks, caching, matrices, test
  reporting, security, and trusted actions. Use when creating, changing, or
  reviewing workflow files.
---

# GitHub Actions

Produce CI, release, and deploy workflows that are fast, secure, and leave visible evidence. Repository settings (rulesets, required checks, release permissions) follow the `project-setup` skill.

## Required practices

1. **Conventional Commits.** `type(scope)!: description`. `fix` bumps PATCH, `feat` MINOR, breaking MAJOR. CI validates PR titles for squash-merge repositories (`amannn/action-semantic-pull-request`), or each commit with `commitlint` otherwise.
2. **Tag-driven releases.** Tags `vMAJOR.MINOR.PATCH` (pre-release `-rc.1`) are created only by the release workflow. Protect `v*` tags with a ruleset. One tag, one release, one set of artifacts.
3. **Keep a Changelog.** `CHANGELOG.md` with an `## [Unreleased]` section that the release workflow promotes to a dated version. Categories: Added, Changed, Deprecated, Removed, Fixed, Security. GitHub Release notes are generated separately.

## Workflows

| Workflow | File | Trigger | Job |
| --- | --- | --- | --- |
| CI | `ci.yml` | `push` to default branch, `pull_request`, `merge_group` | Validate. Never publishes. |
| Release | `release.yml` | The project's release policy; `workflow_dispatch` when none is set | Version, tag, release, publish |
| Deploy (optional) | `deploy.yml` | `release` or `workflow_dispatch` | Promote a release to an environment |

## CI rules

- Parallel jobs, no `needs` without a real dependency: commit lint (PRs only), lint, test, build (no publish). Add a `ci-pass` aggregator job as the single required check ([advanced-patterns.md](references/advanced-patterns.md)).
- Explicit top-level `permissions` (CI: `contents: read`, `checks: write`, `pull-requests: read`).
- `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }`. Releases use `cancel-in-progress: false`.
- `paths-ignore` for docs on `push` only. On `pull_request` it can block required checks.
- `timeout-minutes` on every job, at 2-3 times the expected duration.
- Linux runners unless the project needs another OS (Windows costs 2x, macOS 10x).
- Matrices use `fail-fast: false`, only supported combinations, and descriptive job names. Collect coverage on one leg and enforce the threshold with the ecosystem tool.
- Use setup actions' built-in caching before manual `actions/cache`.
- Emit JUnit XML and publish it with a reporter in an `if: always()` step. A green run with no visible test results counts as no tests ([presentation.md](references/presentation.md)).

## Release sequence

Strictly in order; any failure stops the run:

1. Checkout with `fetch-depth: 0`.
2. Compute the next version from commits since the last tag (dry run).
3. Stop if nothing is releasable, unless a force-patch input is set.
4. Run the full lint and test suite.
5. Promote `[Unreleased]` in `CHANGELOG.md`, checking the section exists before and the new header after.
6. Bump version files (`package.json`, `pyproject.toml`, and so on).
7. Build artifacts.
8. Commit all changed files as the bot, tag, and push both together.
9. Create the GitHub Release with artifacts and generated notes.
10. Publish to registries, preferring OIDC trusted publishing.

The release push needs a ruleset bypass or a GitHub App token. Full YAML is in [release-automation.md](references/release-automation.md).

## Security

- Never put `${{ github.event.* }}` user-controlled values (titles, branch names, bodies) directly in `run:`. Pass them through `env:`.
- Never use `pull_request_target` with a checkout of PR code. Use the two-workflow pattern.
- Grant `id-token: write` and other write scopes per job, only where needed.
- `GITHUB_TOKEN` events do not trigger other workflows. Use a GitHub App token when one must.
- Pin actions to the latest major tag, or to a full SHA in release workflows. Verify the tag exists and the action runs on `node24` before using it. Never set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE*` or `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION`.
- Use only trusted, maintained actions ([actions.md](references/actions.md)), and enable Dependabot for `github-actions`.

Details: [security.md](references/security.md).

## Avoid

Manual or tag-triggered releases, publishing without tests, default permissions, `continue-on-error: true` to hide failures, `version: latest` in lint actions, mixing CI and release, and stale action majors.

## Checklist

- [ ] `actionlint` passes on every changed workflow.
- [ ] Each `uses:` is on its latest major, verified with `gh api repos/<owner>/<repo>/releases/latest`.
- [ ] README has CI, Release, and License badges under the title ([presentation.md](references/presentation.md)).

## References

- [ci-workflow-examples.md](references/ci-workflow-examples.md): read for a complete CI workflow per ecosystem (Gradle, Python with uv, Node.js, Go, Rust, .NET).
- [release-automation.md](references/release-automation.md): read when writing a release or deploy workflow, attestation, or recovery steps.
- [advanced-patterns.md](references/advanced-patterns.md): read for reusable workflows, composite actions, the `ci-pass` job, fork PRs, dynamic matrices, monorepos, and debugging.
- [security.md](references/security.md): read when setting permissions, tokens, publishing auth, or action pinning.
- [actions.md](references/actions.md): read when choosing an action.
- [presentation.md](references/presentation.md): read when adding test reporters, job summaries, annotations, or README badges.
