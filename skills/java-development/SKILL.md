---
name: java-development
description: >-
  Conventions for JVM projects (Java, Kotlin, Android) built with Gradle:
  module and package naming, ports-and-adapters architecture, convention
  plugins, strict linting, the full test pyramid, quality gates, and CI. Use
  when creating, restructuring, or reviewing a JVM codebase or its build.
---

# Java development

Structure JVM projects so names reveal location, business rules test without frameworks, and CI proves every change. Where Java and Kotlin differ, both tools are named.

## Module and package naming

- Prefix every module with the root project name: `spam-sweep-core-domain`, `spam-sweep-app`, `spam-sweep-build-logic`.
- Directories are flat and equal the module name (`spam-sweep-core-domain/`, not `core/domain/`).
- Each module owns one top-level package derived from its name: group reverse domain + root name without hyphens + remaining segments. `spam-sweep-core-domain` → `io.github.<owner>.spamsweep.core.domain`.
- No module's package contains another's. The app module gets `….app`, never the bare root package. Android `namespace` equals the package; `applicationId` may differ.
- Group by layer in the name: `-core-*`, `-data-*`, `-platform-*`, `-feature-*`, `-app`, `-tools-*`, `-architecture-tests`.
- Enforce naming with an architecture test (Konsist or ArchUnit) that maps each file's path to its module, checks the package, checks no prefix overlap, and fails if it scanned suspiciously few files.

## Architecture

Ports and adapters around a pure domain ([architecture.md](references/architecture.md)):

- `-core-domain`: pure language. Valid-by-construction value objects, aggregates that change only through checked transitions, pure state machines.
- `-core-application`: use cases and the ports they need. Inject a `Clock`; never read system time.
- `-data-*`, `-platform-*`: one technology per adapter, named for it. Adapters never depend on each other or on UI.
- `-feature-*`: UI and view models, depending only on the application layer.
- `-app`: the composition root, with manual constructor injection until the graph is large.
- `-core-testing`: in-memory fakes for every port, used instead of mocking frameworks.
- Side effects survive process death and replays: persist intent before acting, store waits as data, make inputs idempotent.
- Record decisions and rejected alternatives in `docs/architecture.md`.

## Build and quality

Details in [build.md](references/build.md).

- Gradle Kotlin DSL with the wrapper. Every version in `gradle/libs.versions.toml`, at the latest stable release, checked to exist before pinning.
- All build policy in convention plugins in an included `<root>-build-logic` build. Module build files declare only what is unique.
- Warnings are errors. Kotlin: explicit API mode in libraries. Java: `-Werror -Xlint:all`.
- Linters fail `check`. Kotlin: ktlint (Compose rules) and detekt. Java: Spotless (Palantir or Google format), Checkstyle, Error Prone with NullAway. Android: Lint with `warningsAsErrors`.
- One tool per concern. Every suppression carries a reason.
- Document public API (KDoc or Javadoc); library modules enforce it.
- One aggregate task, `verifyAll`, runs everything except device tests.

## Testing

Details in [testing.md](references/testing.md).

- Cover each layer with its kind of test: unit, use case against fakes, integration with real storage and migrations, adapter (Robolectric), UI with accessibility checks, UX journey, end-to-end on an emulator, architecture, performance (budget test plus JMH), and mutation (PIT).
- Gates fail the build: per-module line coverage (core ≥ 95%) and mutation score (domain ≥ 85%). A lower threshold needs a written reason.
- Classification logic gets a shared, anonymised corpus with one expectation per sample.
- Device and destructive tests never touch a personal device. Target emulators explicitly with `ANDROID_SERIAL`, and refuse to run settings-changing tests on real hardware.

## CI

Details in [ci.md](references/ci.md).

- Run every suite as a parallel job, including mutation, performance, the emulator matrix (minSdk, mid, targetSdk), and installer tests. One aggregate `CI passed` job is the required check.
- Every job leaves evidence: JUnit checks, SARIF in code scanning, coverage and mutation tables in the job summary, reports and checksummed binaries as artifacts.
- Cache with setup-gradle (build cache, encrypted configuration cache, AVD snapshots); only the default branch writes the cache.
- Build Scans publish only from CI, only after the owner opts in through a repository variable, with identifying data obfuscated.
- Never accept third-party terms, publish, or push for the user. Put each such choice behind a variable the user sets.
- Lint workflows with actionlint. Document every variable and secret in `docs/ci.md`.

## Repository hygiene

- Ignore build outputs, `local.properties`, keystores, and JVM crash dumps (`hs_err_pid*.log`, `replay_pid*.log`), which leak local paths. Purge committed dumps from unpushed history.
- `.gitattributes`: LF for `*.sh`, `*.bats`, `*.py`, `gradlew`, and extensionless launchers; CRLF for `*.bat` and `*.cmd`. Commit scripts executable.
- Keep docs generic and anonymise real data ([docs-and-tooling.md](references/docs-and-tooling.md)).
- Commit in reviewable conventional-commit steps. Never push or publish without the user's go-ahead.

## References

- [architecture.md](references/architecture.md): read when designing modules, ports, or side-effect handling.
- [build.md](references/build.md): read when setting up Gradle, convention plugins, compiler flags, or linters.
- [testing.md](references/testing.md): read when adding tests, quality gates, or device tests.
- [ci.md](references/ci.md): read when writing or reviewing GitHub Actions workflows.
- [docs-and-tooling.md](references/docs-and-tooling.md): read when writing `docs/`, generating screenshots, or building an installer script.
