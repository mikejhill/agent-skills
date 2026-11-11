---
name: project-setup
description: Establish or review a project's foundational structure, collaboration, quality checks, testing, and releases. Use for new repositories or policy design; hosting, language, and team profiles supply concrete controls.
---

# Project setup

Build the smallest maintainable project that its users can discover, run, test, and release.

## Establish the foundation

- Inspect existing conventions and applicable profiles before changing structure. Preserve working ecosystem conventions.
- Keep responsibilities modular. Separate reusable logic from delivery interfaces and external integrations; avoid layers without a concrete purpose.
- Put purpose, audience, quick start, supported use, and canonical documentation links in root `README.md`. Verify commands before presenting them as working.
- Use `docs/` for deeper project knowledge. Apply project-documentation conventions when available; use technical-writing for wording in any location.
- Keep conventional root files where tools expect them: `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, and `AGENTS.md` as applicable. Create only files with a real purpose. Confirm license intent rather than inventing it.
- Keep build/package manifests and tool configuration at their conventional paths. Profiles choose source/test layout, lockfiles, formatters, and language tools.
- Ignore local secrets, build outputs, and temporary artifacts. Use the existing temporary-storage convention. Do not commit credentials or private organizational examples.

## Collaboration and quality

- Integrate changes through reviewable proposals, including changes by the owner. Protect shared history and resolve review discussions before integration; profiles define host controls and approval requirements.
- Require reproducible quality and security evidence for the revision being integrated. Verify check identities and reporting tools before making them required. Keep any authorized quality exception narrow and auditable; it must not weaken an independent security gate.
- A proposed policy is not authority to change repository security settings, permissions, or publishing controls. Apply such changes only within the user's explicit authorization; otherwise deliver the concrete proposal and readiness gaps.
- For GitHub-hosted projects, read [references/github.md](references/github.md) when designing or applying the collaboration/release profile. Other hosts use equivalent capabilities through their own profiles; do not import GitHub settings into them.

## Tests and releases

- Make core tests deterministic, isolated, and reproducible through the same documented commands locally and in CI. Pin the necessary runtime and dependency inputs.
- Cover observable behavior, error paths, and meaningful boundaries. Use integration tests at real boundaries; keep mocks from becoming the behavior being tested.
- Separate fast PR feedback from expensive analysis. Run mutation testing asynchronously on the default branch, without making it an eager PR gate.
- Compare a complete, valid mutation score with the configured required threshold. Create or update a durable score finding only when the score is **below** that threshold. Equality passes. Passing survivors remain in reports. Deduplicate findings and retain run/commit evidence.
- Treat crashed, incomplete, missing, or invalid mutation results as separate execution failures. Never infer a passing score or classify them as score findings. If the threshold is undefined, report the configuration gap instead of inventing one.
- Version released behavior consistently and record user-visible changes. Identify the source revision, build inputs, and produced artifacts.
- Build artifacts reproducibly where practical. Verify installation and essential behavior of the actual distributable before publication; test-only source runs do not verify the package.
- Automate versioned releases from verified source and artifacts without adding manual approval gates by default. Separate release creation from deployment; preserve explicitly required approvals and the established release scheme.
- Prefer short-lived, narrowly scoped publishing identity, verifiable build provenance, and least-privilege jobs. Isolate sensitive permissions from untrusted changes; retain rollback and artifact-integrity controls. Profiles supply registry and host details.

## Extend deliberately

Use principles → conventions → profiles. This skill supplies principles; profiles supply language, tool, team, or enterprise choices. State scope and explicit overrides. Do not impose an enterprise tree on a personal repository or silently resolve contradictory applicable profiles. Report conflicts with their sources and proceed only on unaffected work.
