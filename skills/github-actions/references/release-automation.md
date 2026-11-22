# Release Automation Reference

Complete release workflow patterns for the GitHub Actions skill.
This reference provides the full workflow template and
ecosystem-specific publishing snippets.

## Complete Release Workflow Template

This template implements the full release sequence. Adapt it to your
ecosystem by replacing the validation, build, and publish steps.

### Language-Agnostic Core

```yaml
name: Release

on:
  workflow_run:
    workflows: [CI]
    types: [completed]

permissions: {}

# Serialize the whole release sequence, downstream publish and deploy jobs
# included. Ineligible CI completions (PRs, feature branches, failures) get
# their own unique group, so they never enter or displace the release queue.
# A newer pending release replacing an older one is safe: it contains it.
concurrency:
  group: >-
    ${{ github.event.workflow_run.conclusion == 'success' &&
        github.event.workflow_run.event == 'push' &&
        github.event.workflow_run.head_branch == github.event.repository.default_branch &&
        'release' || format('release-skip-{0}', github.run_id) }}
  cancel-in-progress: false

jobs:
  # Read-only gate: exact, case-sensitive branch match before any
  # privileged job starts. (Expression `==` ignores case.)
  gate:
    if: >-
      github.event.workflow_run.conclusion == 'success' &&
      github.event.workflow_run.event == 'push'
    runs-on: ubuntu-latest
    timeout-minutes: 2
    outputs:
      ok: ${{ steps.check.outputs.ok }}
    steps:
      - id: check
        env:
          HEAD_BRANCH: ${{ github.event.workflow_run.head_branch }}
          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
        run: |
          if [ "$HEAD_BRANCH" = "$DEFAULT_BRANCH" ]; then ok=true; else ok=false; fi
          echo "ok=$ok" >> "$GITHUB_OUTPUT"

  release:
    needs: gate
    if: needs.gate.outputs.ok == 'true'
    # Grant every scope this job needs here: a job-level map replaces the
    # workflow-level one. Add `id-token: write` for npm provenance, and
    # `id-token: write`, `attestations: write`, `artifact-metadata: write`
    # for attestation, only when this job performs them.
    permissions:
      contents: write
    runs-on: ubuntu-latest
    timeout-minutes: 30
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          ref: ${{ github.event.workflow_run.head_sha }}
          fetch-depth: 0

      - name: Determine next version
        id: version
        uses: go-semantic-release/action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          allow-initial-development-versions: true
          dry: true

      # Nothing releasable (docs, chore, ci): later steps skip and the run
      # ends green.

      # ── Validation ──────────────────────────────────────────
      # INSERT: ecosystem-specific lint + test steps here.
      # These must pass before any release artifacts are created.
      # Add `if: steps.version.outputs.version != ''` to every step
      # from here on, so non-releasable pushes skip them.
      # ────────────────────────────────────────────────────────

      - name: Validate CHANGELOG structure
        if: steps.version.outputs.version != ''
        run: |
          grep -q "^## \[Unreleased\]" CHANGELOG.md || {
            echo "::error::CHANGELOG.md missing [Unreleased] section"
            exit 1
          }

      - name: Update CHANGELOG.md
        if: steps.version.outputs.version != ''
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          # CHANGELOG.md MUST use LF line endings — sed fails on CRLF
          DATE=$(date -u +%Y-%m-%d)
          sed -i "s/^## \[Unreleased\]$/## [Unreleased]\n\n## [$VERSION] - $DATE/" CHANGELOG.md
          grep -q "## \[$VERSION\]" CHANGELOG.md || {
            echo "::error::CHANGELOG.md update failed — version header not found after sed"
            exit 1
          }

      # ── Build ───────────────────────────────────────────────
      # INSERT: ecosystem-specific build steps here.
      # ────────────────────────────────────────────────────────

      - name: Commit release changes and push tag
        if: steps.version.outputs.version != ''
        env:
          VERSION: ${{ steps.version.outputs.version }}
          BRANCH: ${{ github.event.repository.default_branch }}
          VERIFIED_SHA: ${{ github.event.workflow_run.head_sha }}
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git commit -m "chore(release): v$VERSION"
          git tag "v$VERSION"
          # The lease rejects the push if the branch moved since CI
          # verified this commit, forward or back. Forward is safe: CI
          # runs on every default-branch push (no paths-ignore), and its
          # release run includes these changes. After a rollback, nothing
          # is pushed. GITHUB_TOKEN pushes do not trigger CI, so no loop.
          git push --atomic --force-with-lease="refs/heads/$BRANCH:$VERIFIED_SHA" \
            origin "HEAD:refs/heads/$BRANCH" "v$VERSION"

      - name: Create GitHub Release
        if: steps.version.outputs.version != ''
        uses: softprops/action-gh-release@v2
        with:
          tag_name: "v${{ steps.version.outputs.version }}"
          name: "v${{ steps.version.outputs.version }}"
          generate_release_notes: true
          files: |
            dist/*

      # ── Publish ─────────────────────────────────────────────
      # INSERT: ecosystem-specific publish steps here,
      # or use a separate job (see OIDC patterns below).
      # ────────────────────────────────────────────────────────
```

### Trigger notes

- `workflow_run` fires only from the workflow file on the default branch, and `workflows:` must match the CI workflow's `name:` exactly. The gate compares `head_branch` with the repository's default branch in shell, case-sensitively, so no branch name is hard-coded.
- Only successful `push` runs of CI on the default branch qualify, so PR and feature-branch runs never release. CI must run on every default-branch push, with no `paths-ignore`, or a docs-only push can strand a pending release.
- There is no manual trigger: every release comes from a CI-verified commit. To release when no `feat`/`fix` commit is pending, merge one (for example `fix: ...` for the change that warrants it).
- Every merged `feat`/`fix` releases. To batch releases, merge less often or use a release PR tool such as Release Please; do not add a dispatch button as the gate.

## Ecosystem-Specific Snippets

Replace the placeholder sections in the template above with the
appropriate snippets for your ecosystem.

### Python (UV + PyPI via OIDC)

```yaml
      # ── Validation ──
      - uses: astral-sh/setup-uv@v7
      - run: uv sync --group dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy src
      - run: uv run pytest

      # ── Build ──
      - run: uv build
        env:
          SETUPTOOLS_SCM_PRETEND_VERSION: ${{ steps.version.outputs.version }}

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

PyPI publishing uses OIDC trusted publishers and runs as a separate
job so permissions are scoped. Gate every downstream job on
`needs.release.outputs.version`, so non-releasable pushes publish nothing:

```yaml
  pypi:
    needs: release
    if: needs.release.outputs.version != ''
    runs-on: ubuntu-latest
    timeout-minutes: 10
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### Node.js (npm)

```yaml
      # ── Validation ──
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
          registry-url: https://registry.npmjs.org
      - run: npm ci
      - run: npm run lint
      - run: npm test

      # ── Build ──
      - name: Set version and build
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          npm version "$VERSION" --no-git-tag-version
      - run: npm run build
      - run: npm pack
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: "*.tgz"

      # ── Publish ──
      # npm --provenance requires OIDC: add id-token: write to this
      # job's permissions (workflow-level grants do not reach it).
      - run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

For OIDC-based npm publishing, the job that runs `npm publish` needs
`id-token: write` in its own `permissions` for `--provenance` to work.
Without it, npm publish fails at runtime.

### Gradle (Java/Kotlin)

```yaml
      # ── Validation ──
      - uses: actions/setup-java@v4
        with:
          java-version: 21
          distribution: temurin
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew check

      # ── Build ──
      - name: Build
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: ./gradlew build -Pversion="$VERSION"
      - uses: actions/upload-artifact@v4
        with:
          name: build-artifacts
          path: build/libs/
```

For Maven Central publishing:

```yaml
      # ── Publish (Maven Central) ──
      - name: Publish to Maven Central
        env:
          VERSION: ${{ steps.version.outputs.version }}
          MAVEN_USERNAME: ${{ secrets.MAVEN_USERNAME }}
          MAVEN_PASSWORD: ${{ secrets.MAVEN_PASSWORD }}
          SIGNING_KEY: ${{ secrets.SIGNING_KEY }}
          SIGNING_PASSWORD: ${{ secrets.SIGNING_PASSWORD }}
        run: ./gradlew publish -Pversion="$VERSION"
```

For JetBrains Marketplace publishing:

```yaml
      # ── Publish (JetBrains Marketplace) ──
      - name: Publish to JetBrains Marketplace
        env:
          VERSION: ${{ steps.version.outputs.version }}
          PUBLISH_TOKEN: ${{ secrets.JETBRAINS_TOKEN }}
        run: ./gradlew publishPlugin -Pversion="$VERSION"
```

### Go

```yaml
      # ── Validation ──
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - run: go vet ./...
      - run: go test ./...

      # ── Build ──
      - name: Build binaries
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          GOOS=linux   GOARCH=amd64 go build -ldflags "-X main.version=$VERSION" -o dist/app-linux-amd64 .
          GOOS=darwin  GOARCH=arm64 go build -ldflags "-X main.version=$VERSION" -o dist/app-darwin-arm64 .
          GOOS=windows GOARCH=amd64 go build -ldflags "-X main.version=$VERSION" -o dist/app-windows-amd64.exe .
```

Go modules are published automatically via git tags — no registry
push step is needed. The tag push in the core template is sufficient.

### Rust (crates.io)

```yaml
      # ── Validation ──
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo clippy -- -D warnings
      - run: cargo test

      # ── Build ──
      - name: Set version
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          # Target only the [package] section version to avoid
          # matching dependency version lines in workspace Cargo.toml
          sed -i '0,/^version = ".*"/s//version = "'"$VERSION"'"/' Cargo.toml
      - run: cargo build --release
      - uses: actions/upload-artifact@v4
        with:
          name: release-binary
          path: target/release/

      # ── Publish ──
      - run: cargo publish
        env:
          CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}
```

### .NET (NuGet)

```yaml
      # ── Validation ──
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: 9.x
      - run: dotnet restore
      - run: dotnet build --no-restore
      - run: dotnet test --no-build

      # ── Build ──
      - name: Pack
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: >-
          dotnet pack -c Release
          -p:PackageVersion=$VERSION
          -o dist/

      # ── Publish ──
      - run: >-
          dotnet nuget push dist/*.nupkg
          --api-key ${{ secrets.NUGET_API_KEY }}
          --source https://api.nuget.org/v3/index.json
```

### Docker

```yaml
      # ── Build and Publish ──
      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - uses: docker/build-push-action@v6
        with:
          push: true
          cache-from: type=gha
          cache-to: type=gha,mode=max
          tags: |
            ${{ github.repository }}:v${{ steps.version.outputs.version }}
            ${{ github.repository }}:latest
```

For multi-platform images, add `platforms: linux/amd64,linux/arm64`.
The `cache-from`/`cache-to` with `type=gha` uses GitHub Actions cache
for Docker layer caching, typically providing 5–10× build speedups.

For GHCR (GitHub Container Registry):

```yaml
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
```

## Deployment Patterns

### Environment-Gated Deployments

For projects that deploy to infrastructure (not just publish packages),
use GitHub environments with protection rules:

```yaml
  deploy-staging:
    needs: release
    if: needs.release.outputs.version != ''
    runs-on: ubuntu-latest
    timeout-minutes: 15
    environment: staging
    steps:
      - name: Deploy to staging
        run: echo "Deploy to staging..."

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    timeout-minutes: 15
    environment:
      name: production
      url: https://example.com
    steps:
      - name: Deploy to production
        run: echo "Deploy to production..."
```

Configure each environment in repository settings:

- **staging** — No restrictions (auto-deploys after release)
- **production** — Required reviewers, wait timer, deployment branch
  restrictions (`main` only)

### Multi-Registry Publishing

Some projects publish to multiple registries (e.g., npm + GitHub
Packages, or PyPI + GitHub Packages). Use separate jobs for each, all
depending on the `release` job:

```yaml
  npm:
    needs: release
    if: needs.release.outputs.version != ''
    # ... npm publish steps

  github-packages:
    needs: release
    if: needs.release.outputs.version != ''
    # ... GitHub Packages publish steps
```

## Tag Protection Setup

Configure repository rulesets (Settings → Rules → Rulesets):

1. Create a new ruleset targeting **tags** matching `v*`
2. Under "Bypass list", add only the **GitHub Actions** actor
3. Enable **Restrict creations** and **Restrict deletions**
4. This ensures only the release workflow can create or delete version
   tags

## CHANGELOG.md Template

New projects should start with this file:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
```

## Dependabot Configuration

Keep action versions current automatically:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    commit-message:
      prefix: "ci"
```

This ensures action version updates are proposed as PRs with
conventional commit messages (`ci(deps): bump actions/checkout from
v4.1.0 to v4.2.0`).

## Artifact Attestation

Generate build provenance attestations for release artifacts using
GitHub's official attestation action. This creates a signed,
verifiable record of what was built, by whom, and from which source.

```yaml
      - name: Attest build provenance
        uses: actions/attest@v4
        with:
          subject-path: dist/*
```

Requires `attestations: write`, `artifact-metadata: write`, and
`id-token: write` in the attesting job's own `permissions`. Consumers verify with
`gh attestation verify`.

## Artifact Retention

Set explicit retention periods on uploaded artifacts to control storage
costs:

```yaml
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
          retention-days: 7
```

Use short retention (3–7 days) for CI build artifacts and longer
retention (30–90 days) for release artifacts. The repository default is
90 days.

## Release Failure Recovery

If the release workflow fails mid-execution:

1. **Failed before tag push** — Safe to re-run. No state has been
   published externally.
2. **Failed after tag push but before GitHub Release** — Delete the
   orphan tag (`git push --delete origin v1.2.3`) and re-run.
3. **Failed after GitHub Release but before publish** — Delete the
   GitHub Release and tag, then re-run. Alternatively, manually publish
   the artifacts from the release.
4. **Failed during publish** — The tag and release exist. Manually push
   to the registry using the artifacts from the GitHub Release, or
   re-run only the publish job if the workflow supports it.

Design release workflows to be idempotent where possible: check whether
the tag already exists before creating it, and check whether the package
version already exists before publishing.

## Branch Protection Considerations

The release workflow pushes commits and tags directly to the default
branch. This conflicts with branch protection rules that require PR
reviews or status checks.

Options:

1. **Ruleset bypass** — Add the `github-actions[bot]` actor to the
   bypass list in repository rulesets (preferred).
2. **GitHub App token** — Use a GitHub App installation token
   (`actions/create-github-app-token@v1`) with bypass permissions
   instead of `GITHUB_TOKEN`.
3. **Deploy key** — Use a deploy key with write access (least
   preferred; no audit trail per-workflow).

Document the chosen approach in the repository's contributing guide.
