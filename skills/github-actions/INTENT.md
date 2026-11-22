# Intent

Define GitHub Actions standards for any releasable project, regardless of language, so CI, release, and deploy workflows are fast, secure, and maintainable.

## Goals

1. Every workflow enforces Conventional Commits, tag-driven releases, and Keep a Changelog.
2. CI validates and never publishes; release ships; deploy promotes. The concerns stay separate.
3. Test results and failures are visible on the run page.
4. Workflows resist injection and supply-chain attacks, and stay on current action versions.

## Requirements

- Mandatory practices: Conventional Commits (validated in CI), GitOps tag-driven releases (tags created only by the release workflow), and Keep a Changelog.
- At minimum a CI workflow (`push` and `pull_request`) and a release workflow; deploy is optional.
- Releases are automatic: CI success on the default branch triggers the release workflow. No manual approval gate by default.
- Release steps run strictly in order, with validation before publishing and no partial releases.
- Performance: Linux runners, built-in caching, parallel jobs, concurrency control, path filters, and timeouts.
- Multi-environment matrix builds with `fail-fast: false`.
- JUnit test reporting on every test run, plus job summaries.
- Explicit minimal permissions, no expression injection, safe fork handling, OIDC publishing where available.
- Only trusted, maintained actions, on their latest major versions. No Node-runtime override variables.
- README status badges for CI, Release, and License.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 661 lines (over the 500 limit) to about 100. Security, trusted actions, and presentation (reporters, summaries, badges) moved to new references. The release trigger now follows the project's release policy, with `workflow_dispatch` as the default, because `project-setup`'s GitHub profile prefers automatic releases from verified source. The curated action list is marked as needing verification, since several pins in it lag their latest majors.
- 2026-11-22: [operator] "Release trigger: Prefer automatic releases." Release workflow now runs on `workflow_run` after CI succeeds on a default-branch push; non-releasable pushes end successfully; `workflow_dispatch` kept only for force-patch.
- 2026-11-22: [agent] Codex review fixes on the migration: quoted-safe concurrency rule; node24 check applies only to JavaScript actions.
- 2026-11-22: [agent] Second Codex review fixes: manual release runs require force-patch and passing CI for the same SHA; default branch taken from the repository, not hard-coded; release push leased to the verified SHA; CI examples drop `paths-ignore` so docs-only pushes cannot strand a release.
- 2026-11-22: [agent] Third Codex review fixes: removed the manual release trigger (every release comes from a CI-verified commit); a read-only gate job matches the default branch case-sensitively; release concurrency and write permission moved to the job.
- 2026-11-22: [agent] Fourth (final) Codex review fixes: workflow-level concurrency serializes the whole release, downstream jobs included, while ineligible runs get a unique group; optional OIDC and attestation scopes go on the consuming job.
- 2026-11-22: [agent] Removed named references to other skills and instruction files; adjacent concerns are now described by capability ("any ... standards the user has") so the skill stands alone.
- 2026-11-22: [agent] Codex review: kept the safeguards that used to come from the removed references inline (review-clone cleanup checks and scratch defaults, credential file permissions, verifying release prerequisites).
