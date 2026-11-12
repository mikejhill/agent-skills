# GitHub collaboration and release profile

Read this reference only for GitHub-hosted projects. It defines the requested profile, not standing permission to change repository settings. Resolve the repository, applicable organization rules, and user authorization first. Do not weaken existing controls to make a workflow pass.

## Bind the profile

Record these project-specific choices in the existing project guidance:

| Parameter | Resolve before enforcement |
| --- | --- |
| Integration branch | Actual default branch; often `main`, never assume the name |
| Owner identity | Verified configured owner actor; no universal username or blanket administrator bypass |
| Required CI checks | Exact observed context/job names and expected reporting GitHub App/integration |
| Security tool and thresholds | Working CodeQL configuration and explicit code/security alert severity thresholds |
| Release identity | Approved trigger, source revision/tag, registry project, and trusted workflow identity |
| Automation PR identity | Whether release/bot workflows open PRs, and which token they use (`GITHUB_TOKEN`, GitHub App, or PAT) |

Check platform/plan support and every applicable ruleset. If the requested owner-only identity or security control cannot be represented, report the precise limitation rather than granting a broader role or claiming enforcement.

## Integration rules

Use separate rule boundaries so a CI exception cannot bypass history, review, or security requirements:

| Boundary | Required behavior | Bypass policy |
| --- | --- | --- |
| Integration/history | Pull request required for everyone, including owner; block force pushes and deletion; require linear history and resolved review conversations | None |
| CI | Require the verified CI contexts for the candidate revision | None by default; only the configured owner may bypass CI through a PR if explicitly configured and authorized |
| Security | Require verified CodeQL code-scanning results at the configured thresholds | None, including owner and automation |

- The profile target is **0** mandatory approving reviews. Preserve an existing explicit approval mandate unless the user authorizes replacing it; report that conflict before claiming the target is met. PRs and resolved threads still apply; voluntary review remains useful. Do not fabricate an approving review to satisfy a gate.
- Select compatible linear merge methods, such as squash or rebase. Do not enable merge commits that defeat the linear-history requirement.
- Keep owner CI bypass in a CI-only ruleset with GitHub's **For pull requests only** mode when supported. Never add the actor to the structural or security boundary. An owner exception is not permission to push directly, force-push, delete the branch, or bypass CodeQL.
- Read back active rules, inherited controls, bypass actors/modes, and check bindings. Verify their combined behavior; a saved ruleset is not proof that the intended checks run.

## Checks must be ready first

1. Implement and run the actual workflows before adding required checks. Discover exact reported names and trusted reporting integration from successful runs; do not guess workflow titles or invent status contexts.
2. Verify PR triggers, paths, matrix outcomes, and merge-queue triggers where used. Required results must cover the revision being integrated and cannot disappear on routine path filters. A summary check must propagate failures and missing/incomplete required jobs.
3. Confirm CodeQL analyzes the relevant supported languages, uploads usable results, and can evaluate PRs at the configured severity thresholds. A green analysis/upload job alone is not proof that a code-scanning merge gate enforces alert policy.
4. If tool availability, permissions, language support, or plan support is missing, report the readiness gap. Do not enforce a nonexistent check, invent a pass, silently substitute a weaker tool, or claim a security gate is verified.
5. Apply authorized controls only after these prerequisites are ready. Read back configuration and inspect real candidate results without using unsafe live branch operations as tests.

Mutation testing remains asynchronous on the default branch, outside required merge checks. Use the core skill's score rule: durable score alerts only below the configured threshold; equality and higher scores keep survivors in reports. Failed or incomplete execution raises a separate infrastructure/execution alert, never a score pass or score finding. Keep evidence and deduplicate alerts.

## Automated releases and sensitive jobs

- Choose a reproducible automatic release trigger for verified source, such as the project's version/tag policy. A dispatch button is not the default approval gate. Do not add required environment reviewers unless an explicit project requirement calls for them; preserve already-required approvals until authorized to change them.
- Publish the tested artifacts associated with the verified source revision. Check artifact hashes and provenance against the expected repository, workflow identity, revision, and artifact; provenance does not replace functional/package tests.
- Prefer registry-supported OIDC trusted publishing over long-lived upload secrets. Bind trust narrowly to the approved repository, workflow, and registry project, plus environment/ref constraints where supported. Confirm actual registry trust before publishing.
- Grant `id-token: write` only to the publishing/attestation job that needs it. Give release, attestation, security-upload, and repository writes only their required scopes. Keep ordinary checks read-only; do not grant broad permissions globally.
- Use reviewed, pinned actions and supported publisher versions. Keep privileged jobs isolated from untrusted PR code, artifacts, and inputs; never run untrusted checkout code with sensitive tokens merely to obtain a check result.
- This profile does not authorize publishing, changing a trusted publisher, adding credentials, changing repository permissions, or using an owner exception. Those actions still require task-specific authorization.

## Workflows that open pull requests

Release Please, dependency bumpers, and similar bots open PRs from Actions. GitHub blocks this by default, so a new repository fails with `GitHub Actions is not permitted to create or approve pull requests`. Configure it during setup instead of opening those PRs by hand.

1. **Repository setting.** Enable *Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests*. Keep the default token read-only; grant writes per job.

   ```bash
   gh api -X PUT "repos/$OWNER/$REPO/actions/permissions/workflow" \
     -f default_workflow_permissions=read \
     -F can_approve_pull_request_reviews=true
   gh api "repos/$OWNER/$REPO/actions/permissions/workflow"   # read back
   ```

   `can_approve_pull_request_reviews` is the API name for the create-and-approve checkbox. It needs repository admin. Approval stays harmless under this profile because mandatory approvals are 0; never use it to satisfy a required review.
2. **Job permissions.** Grant only the PR-opening job `contents: write` and `pull-requests: write` (add `issues: write` when the tool manages labels, as Release Please does).

   ```yaml
   jobs:
     release-please:
       runs-on: ubuntu-latest
       permissions:
         contents: write
         pull-requests: write
         issues: write
       steps:
         - uses: googleapis/release-please-action@v4
           with:
             token: ${{ secrets.RELEASE_PLEASE_TOKEN || github.token }}
   ```

3. **Organization policy.** If the PUT returns `409` or the checkbox is greyed out, the organization or enterprise disables it. Ask an org owner to allow it (*Organization settings → Actions → General → Workflow permissions*), or use the fallback below. Do not report the setup complete while the PR path is blocked.
4. **Required checks.** PRs and pushes made with `GITHUB_TOKEN` do not trigger other workflows, so required CI never reports on the release PR and it cannot merge. If the release PR must pass required checks, use the fallback token from the start.
5. **Fallback token.** Prefer a GitHub App installed only on this repository with *Contents* and *Pull requests* read/write; mint a short-lived token per run with `actions/create-github-app-token` and pass it as `token`. A fine-grained PAT scoped to the one repository with the same permissions is acceptable for personal repositories; store it as a repository secret (for example `RELEASE_PLEASE_TOKEN`) and record its expiry. Never use a classic PAT with `repo` scope. Adding an App, PAT, or secret needs user authorization like any other credential change.
6. **Verify.** Run the workflow once (`gh workflow run` or a qualifying push) and confirm the bot PR opens and its required checks report. A saved setting is not proof.

## Implementation references

Consult current primary documentation before changing platform controls; availability and APIs can change:

- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets): integration, history, and check rules.
- [Creating rulesets and bypass lists](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository): actor scope and PR-only bypass mode.
- [Code-scanning merge protection](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/manage-your-configuration/set-merge-protection): tool readiness and severity thresholds.
- [OIDC with PyPI](https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi): one registry-specific trusted publishing example, not a mandate to use PyPI.
- [Managing GitHub Actions settings for a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#preventing-github-actions-from-creating-or-approving-pull-requests): the create/approve PR setting and org overrides.
- [Triggering a workflow from a workflow](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#triggering-a-workflow-from-a-workflow): why `GITHUB_TOKEN` events do not start CI.
- [Artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations): provenance generation and verification.
