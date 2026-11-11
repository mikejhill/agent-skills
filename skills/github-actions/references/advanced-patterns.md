# Advanced Patterns

Advanced GitHub Actions patterns for the GitHub Actions skill.
This reference covers reusable workflows, composite actions, the ci-pass
aggregator pattern, GITHUB_TOKEN scope,
fork pull request handling, and debugging.

## Reusable Workflows

Reusable workflows (`workflow_call`) are the native DRY mechanism for
GitHub Actions. Use them to share CI logic across repositories.

### Defining a Reusable Workflow

```yaml
# .github/workflows/reusable-ci.yml
name: Reusable CI

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: "22"
      working-directory:
        type: string
        default: "."
    secrets:
      NPM_TOKEN:
        required: false

permissions:
  contents: read
  checks: write

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: npm
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: npm
      - run: npm ci
      - run: npm test
```

### Calling a Reusable Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  merge_group:

jobs:
  ci:
    uses: my-org/.github/.github/workflows/reusable-ci.yml@main
    with:
      node-version: "22"
    secrets: inherit
```

### Guidelines

- Store reusable workflows in an organization `.github` repository
  for maximum sharing.
- Pin to a branch or tag, not `@main` in production, to avoid
  unexpected changes.
- Use `secrets: inherit` only when the caller trusts the reusable
  workflow completely. Prefer explicit secret passing otherwise.
- Reusable workflows count toward the 20-workflow nesting limit and
  the 4-level depth limit.

## Composite Actions

Composite actions package multiple steps into a single reusable action.
Use them for step-level reuse within a job (as opposed to reusable
workflows which share entire jobs).

```yaml
# .github/actions/setup-and-build/action.yml
name: Setup and Build
description: Install dependencies and build the project

inputs:
  node-version:
    description: Node.js version
    default: "22"

runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: npm
    - run: npm ci
      shell: bash
    - run: npm run build
      shell: bash
```

Usage in a workflow:

```yaml
steps:
  - uses: actions/checkout@v6
  - uses: ./.github/actions/setup-and-build
    with:
      node-version: "22"
```

## ci-pass Aggregator Job

The ci-pass pattern creates a single, stable status check name that
branch protection rules reference. This decouples protection from
individual job names, so adding or renaming matrix entries never breaks
merge requirements.

```yaml
  ci-pass:
    if: always()
    needs: [commit-lint, lint, test, build, markdown]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Verify all jobs passed
        run: |
          if [[ "${{ contains(needs.*.result, 'failure') }}" == "true" ]]; then
            echo "::error::One or more required jobs failed"
            exit 1
          fi
          if [[ "${{ contains(needs.*.result, 'cancelled') }}" == "true" ]]; then
            echo "::error::One or more required jobs were cancelled"
            exit 1
          fi
```

Configure branch protection to require only the `ci-pass` status
check. All other jobs feed into it via `needs`.

### Handling Skipped Jobs

Jobs with `if` conditions (like `commit-lint` which only runs on PRs)
report `skipped` status when the condition is false. The `contains()`
check above passes for skipped jobs because `skipped` is neither
`failure` nor `cancelled`.

## GITHUB_TOKEN Scope and Limitations

### Cannot Trigger Other Workflows

Events created with `GITHUB_TOKEN` do not trigger other workflows.
This means:

- A release workflow that pushes a tag using `GITHUB_TOKEN` will NOT
  trigger a `on: push: tags` workflow.
- A workflow that creates a release using `GITHUB_TOKEN` will NOT
  trigger a `on: release` workflow.

### Workarounds

1. **GitHub App installation token** — Use
   `actions/create-github-app-token@v1` to generate a token from a
   GitHub App. Events created with this token DO trigger other
   workflows.
2. **Fine-grained PAT** — Use a personal access token with minimum
   required scopes. Less preferred because it's tied to a user account.
3. **Single workflow** — Keep all release steps (build, tag, publish,
   deploy) in one workflow to avoid the trigger limitation entirely.

### Token Permissions Reference

| Workflow type     | Required permissions                              |
| ----------------- | ------------------------------------------------- |
| CI (read-only)    | `contents: read`, `checks: write`                 |
| CI (PR comments)  | `contents: read`, `pull-requests: write`           |
| Release           | `contents: write`                                 |
| OIDC publish      | `contents: write`, `id-token: write`              |
| Attestation       | `contents: write`, `id-token: write`, `attestations: write` |
| Deployment        | `contents: read`, `deployments: write`            |

## Fork Pull Request Security

### The Problem

Pull requests from forks run with restricted permissions:

- `GITHUB_TOKEN` is read-only
- Repository secrets are not available
- Organization secrets are not available

This is a security feature — fork code cannot access secrets.

### The Dangerous Workaround

`pull_request_target` runs in the context of the base repository with
full secrets access. If the workflow checks out the PR's code
(`actions/checkout` with `ref: ${{ github.event.pull_request.head.ref }}`),
fork code executes with write permissions and secret access.

**Never use `pull_request_target` with a checkout of the PR branch.**

### The Safe Two-Workflow Pattern

1. **CI workflow** (`pull_request`) — Runs lint and tests. No secrets
   needed. Uses `GITHUB_TOKEN` read-only permissions.
2. **Post-CI workflow** (`workflow_run`) — Triggered after the CI
   workflow completes. Runs in the base repository context with full
   permissions. Performs actions that need secrets (e.g., publishing
   test results as PR comments, updating deployment previews).

```yaml
# .github/workflows/post-ci.yml
name: Post-CI

on:
  workflow_run:
    workflows: [CI]
    types: [completed]

permissions:
  pull-requests: write
  checks: write

jobs:
  report:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
      # Process artifacts and post results
```

## Debugging Workflows

### Enable Debug Logging

Set the `ACTIONS_STEP_DEBUG` secret to `true` in the repository to
enable verbose step output for all workflows. This reveals internal
action logs and expanded environment details.

Alternatively, re-run a specific workflow with debug logging enabled:

1. Go to the workflow run page
2. Click "Re-run all jobs"
3. Check "Enable debug logging"

### Runner Diagnostic Logging

For deeper runner-level diagnostics, set the `ACTIONS_RUNNER_DEBUG`
secret to `true`. This produces extremely verbose output about the
runner environment and is typically only needed when investigating
runner infrastructure issues.

### Local Testing with `act`

Use [nektos/act](https://github.com/nektos/act) to run workflows
locally during development:

```bash
# Run the default push event
act

# Run a specific workflow
act -W .github/workflows/ci.yml

# Run with a specific event
act pull_request

# List available workflows
act -l
```

Limitations: `act` does not support all GitHub Actions features
(services, caching, artifacts). Use it for fast iteration on workflow
logic, not as a complete replacement for CI.

### Common Debugging Steps

```yaml
- name: Debug context
  if: runner.debug == '1'
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "Actor: ${{ github.actor }}"
    cat "$GITHUB_EVENT_PATH" | jq '.'
```

## Dynamic Matrices

Generate matrix entries dynamically when the set of targets varies
(e.g., monorepo packages, discovered test suites):

```yaml
jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.find.outputs.packages }}
    steps:
      - uses: actions/checkout@v6
      - id: find
        run: |
          PACKAGES=$(ls -d packages/*/  | jq -R -s -c 'split("\n") | map(select(length > 0))')
          echo "packages=$PACKAGES" >> "$GITHUB_OUTPUT"

  test:
    needs: discover
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: ${{ fromJSON(needs.discover.outputs.packages) }}
    steps:
      - uses: actions/checkout@v6
      - run: npm test --prefix "${{ matrix.package }}"
```

## Monorepo Path Filtering

For monorepos, use `dorny/paths-filter@v3` or the built-in `paths`
filter to run only relevant jobs:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
    steps:
      - uses: actions/checkout@v6
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            frontend:
              - 'frontend/**'
            backend:
              - 'backend/**'

  frontend-ci:
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    # ... frontend CI jobs

  backend-ci:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    # ... backend CI jobs
```

## Retry Strategies

For flaky external dependencies (network calls, registry pulls), use
retry logic:

```yaml
- name: Publish with retry
  uses: nick-fields/retry@v3
  with:
    timeout_minutes: 5
    max_attempts: 3
    retry_wait_seconds: 10
    command: npm publish --provenance --access public
```

Reserve retries for external system interactions only. Never retry
test or lint failures — those indicate real problems.
