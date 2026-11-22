# Intent

Build the smallest maintainable project that its users can discover, run, test, and release, with principles that apply to any host or language and profiles that supply concrete controls.

## Goals

1. New and existing repositories get consistent foundations without overriding working conventions.
2. Every change, including the owner's, integrates through a reviewable proposal with verified quality and security evidence.
3. Releases are automated from verified source and artifacts, with least-privilege identities.
4. No policy change happens without the user's explicit authorization.

## Requirements

- Layering: principles, then conventions, then profiles. This skill supplies principles; profiles (hosting, language, team, enterprise) supply concrete controls. Do not impose an enterprise tree on a personal repository.
- Root files only where they have a real purpose; confirm license intent.
- PRs required for everyone, including the owner. Protected history: linear, no force-push or deletion, resolved conversations. Mandatory approving reviews: 0 by default.
- Required checks only after the real workflows run and report verified names. CodeQL security gate with no bypass.
- Owner may bypass CI only, through PRs only, when configured and authorized.
- Mutation testing runs asynchronously on the default branch, not as a PR gate. Alert only when a valid score is below the threshold; execution failures are separate alerts.
- Automated releases without manual approval gates by default. Bot workflows (Release Please, dependency bumpers) must be able to open PRs, and their required checks must run.
- OIDC trusted publishing, narrowly scoped write permissions, provenance checks.
- Report unsupported controls or readiness gaps instead of claiming enforcement.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill and its GitHub profile.
- 2026-11 (PR #8): GitHub Actions workflows may open release PRs; setup configures this instead of opening bot PRs by hand.
- 2026-11-22: [agent] Migrated to the `skill-development` standard: clearer description, a reference index, README and INTENT. No rule changes.
