# Presentation

## Job Summaries

Write Markdown to `$GITHUB_STEP_SUMMARY` for rich output on the run
page. Use `if: always()` so summaries appear even on failure.

## Test Reporters

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

## Build Scans (Gradle)

`gradle/actions/setup-gradle@v4` links build scans in workflow output
automatically. Add `--scan` to Gradle commands for public URLs.

## Annotations

Use `::error file=path,line=N::message` and `::warning::message`
workflow commands to surface issues inline on files.

## README Badges

Every project with GitHub Actions workflows include status badges
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
