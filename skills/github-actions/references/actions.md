# Trusted actions

Pins below were current when written. Check each with `gh api repos/<owner>/<repo>/releases/latest --jq .tag_name` before use.

## Selection Criteria

Only use actions that meet ALL of these requirements:

- Published by GitHub (`actions/*`), a verified creator, or a
  recognized open-source organization
- Actively maintained — updated within the past 12 months
- Widely adopted — significant community usage and stars
- Open source — auditable code

## Curated List

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
move; see [Action Version Currency](security.md#action-version-currency) for how to
keep them fresh on each repository.

**Avoid** actions with fewer than 100 stars, no updates in 12+ months,
unknown publishers, excessive permission requirements, or functionality
already covered by official `actions/*` actions.
