# Continuous integration (GitHub Actions)

CI is the project's definition of "done". Every test suite in the pyramid runs there, not just the
cheap ones. Every job leaves evidence behind: reports, artifacts and summaries. A reviewer can tell
why something failed without rerunning it.

## Contents

1. Workflow shape
2. Jobs to include
3. Caching
4. Build Scans (Develocity)
5. Reports, artifacts and summaries
6. Testing scripts and installers
7. Security and hygiene
8. Validating the workflows themselves

## 1. Workflow shape

- `ci.yml` triggers on `push` to the default branch, `pull_request`, and `workflow_dispatch`.
  Use `release.yml` for tags, and keep slow manual jobs in their own `workflow_dispatch` workflows.
- Set `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: <true only for PRs> }`.
  Superseded PR runs stop, but `main` runs always finish, so the cache gets written.
- Put least-privilege `permissions: contents: read` at the top. Jobs then add exactly what they need:
  - `security-events: write` for SARIF;
  - `checks: write` for test-report checks;
  - `contents: write` for dependency submission.
- Run independent suites as parallel jobs: build/lint, tests, mutation, performance, end-to-end,
  scripts. Give every job a `timeout-minutes`.
- End with one aggregate job, for example `CI passed`. It `needs:` every gating job, runs `if: always()`,
  and fails unless every result is `success`. Branch protection then requires just that one check,
  however the matrix changes.
- Factor repeated setup into local composite actions (`.github/actions/setup-build`,
  `.github/actions/enable-kvm`). Every workflow then sets up the toolchain and cache the same way.

## 2. Jobs to include

| Job | Gradle | Notes |
|---|---|---|
| Build + static analysis | `assembleDebug assembleRelease assembleDebugAndroidTest`, then `ktlintCheck detekt lint --continue` | Upload the APKs with a `SHA256SUMS` file. Upload SARIF (section 5). |
| Tests + coverage | `test --continue`, then `koverVerify koverXmlReport koverHtmlReport` | Covers unit, integration, Robolectric UI/UX and architecture tests. Publish a JUnit check and a coverage table. |
| Mutation | `pitest` | Put a score table in the summary; use PIT's `detected` flag, as PIT does. |
| Performance | `performanceTest`, then `jmh` | The budget tests are the gate. JMH is informational only: shared runners are too noisy for hard limits. |
| End-to-end | `connectedDebugAndroidTest` on an emulator matrix | Test at minSdk, a common mid version, and targetSdk. Build the APKs before the emulator boots. Cache the AVD snapshot per API level. Set `ANDROID_SERIAL=emulator-5554`. |
| Installer tests | (none) | Run the install scripts against fakes on every OS and shell they claim to support (section 6). |
| Script lint | (none) | shellcheck (including `.bats` files with `--shell=bash`), PSScriptAnalyzer at `-Severity Warning,Error`, actionlint. |
| Dependency review | (none) | Pull requests only: `actions/dependency-review-action`. |
| Dependency submission | (none) | Pushes only: `gradle/actions/dependency-submission`, which feeds Dependabot alerts. |
| Media | `captureMedia` | Default branch only. Upload the result as an artifact, so docs drift is visible. |

Also add `.github/dependabot.yml` for `gradle` and `github-actions`, with grouped weekly updates. List
`directories: ["/", "/.github/actions/*"]` so actions used inside composite actions get updated too.

Pin actions to their current major version, and check what the latest major is before writing the
workflow; don't copy versions from memory. Releases move quickly: in late 2026 these were
`checkout@v7`, `setup-java@v6`, `setup-gradle@v6`, `upload-artifact@v7`, `download-artifact@v8`
and `cache@v6`.

## 3. Caching

- Use `gradle/actions/setup-gradle`. It caches Gradle User Home: dependencies, the wrapper,
  compiled build logic, and the local build cache. Together with `org.gradle.caching=true` in
  `gradle.properties`, jobs reuse each other's task outputs.
- **Cache provider.** The default `enhanced` provider is proprietary: it is free for public
  repositories and in free preview for private ones, under Gradle's terms. Default to
  `cache-provider: basic`, which is MIT-licensed. Let the owner opt into `enhanced` with a
  repository variable. Never accept third-party terms on the user's behalf.
- Only the default branch writes the cache. Pull requests and fan-out jobs (the emulator matrix)
  run with `cache-read-only: true`, so they can't evict the entries `main` relies on.
- **Configuration cache:** pass `cache-encryption-key: ${{ secrets.GRADLE_ENCRYPTION_KEY }}`
  (from `openssl rand -base64 16`). Without a key, setup-gradle doesn't save the configuration
  cache at all.
- Cache anything else that's expensive with `actions/cache`, for example the AVD:
  `~/.android/avd/*` and `~/.android/adb*`, keyed by API level, target and architecture.

## 4. Build Scans (Develocity)

- Apply `com.gradle.develocity` in `settings.gradle.kts`, and configure it there rather than through
  action inputs, so local and CI builds behave the same.
- Publishing to the free scans.gradle.com means agreeing to Gradle's terms of use. That is the
  owner's decision, so gate it:
  - `publishing.onlyIf { ci && agreed }`;
  - `agreed` comes from an environment variable, which the workflow maps from a repository
    variable such as `BUILD_SCAN_TERMS_OF_USE_AGREE`;
  - set `termsOfUseAgree` only when agreed.

  Local builds never publish, unless someone runs `--scan` and agrees.
- Obfuscate the username, hostname and IP addresses. Add a tag (`CI`/`local`), custom values (the
  workflow and job), and a link back to the Actions run.
- Set `uploadInBackground` to false on CI, so the upload finishes before the runner shuts down.
- Tell the user that scans on scans.gradle.com are public to anyone with the link.

## 5. Reports, artifacts and summaries

- Gate steps run with `--continue`, so one failing module doesn't hide the others. Reporting steps
  run with `if: ${{ !cancelled() }}`, so they run after failures too.
- **Tests.** `mikepenz/action-junit-report` reads `**/build/test-results/**/TEST-*.xml` (JVM) and
  `**/build/outputs/androidTest-results/connected/**/*.xml` (device), and adds a check with
  annotations. Use `require_tests: true`, so a suite that silently ran nothing fails.
- **SARIF.** Enable it in the tools:
  - ktlint: `reporters { reporter(PLAIN); reporter(SARIF) }`;
  - Android Lint: `sarifReport = true`;
  - detekt writes SARIF by default.

  Gradle writes one file per module and source set, and GitHub rejects an upload holding several
  runs of the same tool without distinct categories. So merge the files per tool with a small
  script before uploading:
  - make URIs relative to the repository root;
  - drop `ruleIndex` and artifact indexes;
  - de-duplicate the rules.

  Then upload one file per tool with `github/codeql-action/upload-sarif` and a `category`. Skip the
  upload for pull requests from forks, which can't write security events.
- **Job summaries.** Append Markdown to `$GITHUB_STEP_SUMMARY`: coverage per module (from the
  Kover XML), mutation score per module (from PIT's `mutations.xml`), JMH results and APK
  checksums. Keep these generators as scripts under `scripts/ci/`, not inline YAML.
- **Artifacts.**
  - Upload HTML and XML reports for every suite, plus the built binaries, with
    `actions/upload-artifact`.
  - Name artifacts per matrix entry, so they don't collide.
  - Exclude configuration-cache reports, which are noise.
  - Use `if-no-files-found: error` only where a missing file is a bug, such as the APKs.

## 6. Testing scripts and installers

Installers and other user-facing scripts are product code, so test them like it.

- Run the real script in a child process with no terminal attached (`</dev/null`, or input piped from
  `''`). This proves it never hangs on a prompt in automation, and that "no terminal" means "no".
- **Fake the device tool.** Write a small fake `adb` (a Python script, with a `bash` launcher and a
  `.cmd` launcher) that:
  - appends every invocation to a log;
  - keeps device state (installed packages, permissions) in a JSON file;
  - takes behaviour switches from environment variables: several devices, an older SDK, install
    failure codes.

  Tests then assert on the exact commands the script ran, and on what it printed.
- **Fake the network.** Give the script an environment-variable override for its API base (for
  example `SPAMSWEEP_GITHUB_API`). Serve fixtures from a local `http.server` on port 0 that writes its
  address to a file once it is listening. Cover:
  - the latest release, and a specific tag;
  - checksum verified, checksum tampered, and checksum missing;
  - an unknown release (a friendly error, not a raw 404).
- **Frameworks.** Use bats-core for bash and Pester 5+ for PowerShell (Pester 5+ needs a top-level
  `Describe`).
- **Run the suites on every shell and OS the script claims to support:**
  - bash on Linux;
  - bash 3.2 on macOS, the system default;
  - Git Bash on Windows;
  - pwsh on all three;
  - Windows PowerShell 5.1. Run the Pester runner under pwsh, and launch the script under
    `powershell` by choosing the child shell through an environment variable.
- **Normalise paths in assertions on Windows.** Native tools receive Git Bash paths as `C:/…`; use
  `cygpath -m` when it's available.
- **End-to-end:** drive the installers against the real emulator after the device tests. Install,
  then check status for each permission, update with the other script, then uninstall. The script
  must refuse any serial that isn't `emulator-*`.
- **Bugs these tests catch:**
  - Under `set -euo pipefail`, `x="$(grep … | head)"` exits the script **silently** when grep matches
    nothing. Use `|| true` wherever "not found" is a valid outcome.
  - A PowerShell parameter that should work as a bare flag must be a `[switch]`. A `[string]` with
    a default still demands a value (`Missing an argument for parameter`). Put the value in a
    separate parameter (`-Download` plus `-Tag v1.2.3`). Keep bash and PowerShell flags behaving
    identically (`--tag` alone implies `--download`, so `-Tag` alone must too).
  - Wrap network lookups in friendly errors that say what to check: the repository, the tag, and
    whether any release has been published.
  - Check the exit code of every native step (grants, pairing, uninstall) and stop with what failed;
    never print "Done." after a failure. Some tools exit 0 on failure (`adb connect`), so check
    their output too. Give the fake a failure-injection switch (`FAKE_ADB_FAIL=<substring>`) so
    each path is tested.
  - In Windows PowerShell 5.1, `& tool 2>&1` with `$ErrorActionPreference = 'Stop'` turns any
    stderr line into a terminating error, so your friendly message never prints. Run native calls
    with `Continue` in a small wrapper, and judge them by `$LASTEXITCODE`. Only the 5.1 leg of the
    matrix catches this.
  - Require checksums by default. Installing an unverifiable download should need an explicit
    `--allow-unverified` flag, not just a warning.
  - Guard Android-version-specific steps by API level, both in the scripts and in the device tests.
    `POST_NOTIFICATIONS` doesn't exist before API 33, and the minSdk emulator leg is what catches it.

## 7. Security and hygiene

- Never interpolate `${{ secrets.X }}` or untrusted event fields directly into `run:`. Pass them
  through `env:` and reference the shell variable.
- Device jobs run only on emulators; never a self-hosted runner with a personal phone attached.
- Keep `.gitattributes` rules for every script type: `*.sh`, `*.bats`, `*.py`, and extensionless
  launchers use LF; `*.cmd` and `*.bat` use CRLF. Without them, a Windows checkout breaks shellcheck
  and bash with `\r` errors.

## 8. Validating the workflows themselves

- Run actionlint (it uses shellcheck on `run:` blocks when shellcheck is on PATH) locally before
  committing, and in CI.
- Run every new helper script locally against real build output, for example by merging SARIF from
  a deliberately bad file. Run the installer suites locally under each shell available, before
  relying on CI.
- Document the jobs, artifacts, caching, Build Scans, and every repository variable and secret in
  `docs/ci.md`.
