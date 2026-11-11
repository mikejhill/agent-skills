---
name: java-development
description: Conventions for creating, restructuring or reviewing JVM projects (Java, Kotlin, Android) built with Gradle - module and package naming, layered domain-driven architecture, convention plugins, strict linting, the full test pyramid (unit, integration, UI, end-to-end, architecture, performance, mutation), coverage gates, comprehensive GitHub Actions CI (caching, Build Scans, SARIF, artifacts), docs, release and install tooling with tested installer scripts. Use this whenever the user starts a new Java/Kotlin/Android project, adds or renames a Gradle module, sets up build logic, linting or tests, asks how a JVM codebase should be organised, sets up or reviews CI workflows, or reviews one against these standards, even if they don't say "conventions" or name this skill.
---

# Java development

How JVM projects are structured and held to account. These rules come from building a production
Android app end to end; they apply to plain Java and Kotlin libraries and services too. Where a
rule differs by language, the Java and Kotlin tooling are named side by side.

Read the reference files when the task reaches them:

- [references/build.md](references/build.md): Gradle layout, version catalog, convention plugins, compiler strictness, linters.
- [references/testing.md](references/testing.md): the test pyramid, quality gates, and running tests safely.
- [references/ci.md](references/ci.md): GitHub Actions jobs, caching, Build Scans, SARIF and reports, and testing installer scripts.

## 1. Module and package naming

Names should tell you where code lives without opening a build file.

- **Every module is named after the root project.** For root project `spam-sweep`, modules are
  `spam-sweep-core-domain`, `spam-sweep-data-storage`, `spam-sweep-app`, and so on. The included
  build for build logic is `spam-sweep-build-logic`. A module name read in a stack trace, a
  dependency graph or a published artifact identifies its project.
- **Directories are flat and match the module name exactly:** `spam-sweep-core-domain/`, not
  `core/domain/`. Gradle paths are `:spam-sweep-core-domain`, so project accessors are
  `projects.spamSweepCoreDomain`.
- **Each module owns one top-level package, derived exactly from its name.** Take the group's
  reverse domain (`io.github.<owner>`), add the root project name with its hyphens removed
  (`spamsweep`), then each remaining part of the module name becomes a package segment:
  `spam-sweep-core-domain` → `io.github.<owner>.spamsweep.core.domain`,
  `spam-sweep-tools-demo-messages` → `…spamsweep.tools.demo.messages`.
- **Packages never overlap across modules.** No module's package may contain another's. In
  particular, the application module must not sit in the bare root package (`…spamsweep`), because
  every other module would then be "inside" it; give it `…spamsweep.app`. Android `namespace`
  equals the module's package. The user-facing `applicationId` is separate and may stay short.
- **Enforce it with a test**, not by review. Write an architecture test (Konsist for Kotlin,
  ArchUnit for Java) that, for every source file: derives the module from the path, checks the
  package equals or sits under the derived one, checks no module's package prefixes another's, and
  fails if it scanned suspiciously few files (so it can't pass vacuously).

Group modules by layer in their names: `-core-*` (pure), `-data-*`, `-platform-*` (adapters),
`-feature-*` (UI), `-app` (composition root), `-tools-*` (developer tools),
`-architecture-tests`.

## 2. Architecture

Use ports and adapters with a domain-driven core. Business rules must be testable without any
framework.

- **`-core-domain`** is pure language: entities, value objects, aggregates, and domain services. It
  has no framework or coroutine/reactive dependencies.
  - Value objects validate in constructors or factories that return null, so holding one means it's valid.
  - Aggregates change only through methods that check the transition, and return new values.
  - State machines (for example a multi-step protocol) are pure: events in, new state and commands out.
- **`-core-application`** holds the use cases, plus the **ports** (interfaces) they need:
  repositories, gateways, senders, schedulers, and the clock.
  - It depends only on the domain and on coroutines (Kotlin) or `CompletableFuture`/plain threads (Java).
  - Pass a `Clock` everywhere; never read the system time directly.
- **Adapter modules** (`-data-*`, `-platform-*`) implement ports, one technology each, named for
  it: `RoomTriageRepository`, `SmsTextMessageSender`. Adapters never depend on each other or on UI.
- **`-feature-*`** modules hold UI and view models, and depend only on the application layer.
- **`-app`** is the composition root: the one place that knows every concrete class. Prefer manual
  constructor injection in an `AppContainer` until the graph is genuinely large. Give it explicit
  seams (constructor parameters) for the things tests must replace.
- **`-core-testing`** provides an in-memory implementation of every port, plus a harness that wires
  the application layer the same way production does. Use these fakes instead of mocking frameworks.
- **Shared data used by several test suites** (fixtures, sample corpora) goes in its own
  dependency-free module (`-core-corpus`), never copied between suites.

Design side effects to survive process death and replays, because Android (and any server) kills
processes at arbitrary points:

- **Store intent before acting.** Persist the next state, then send the SMS or call the API. A
  crash then leaves an unsent step that a timeout can cover, never a duplicate.
- **Store waits as data, not as scheduler state.** Retry times and pacing gaps live in the
  aggregate. A scheduled job is only a wake-up call that recomputes what may happen now, so an
  early or duplicate wake-up can't skip a wait.
- **Make inputs idempotent.** Record the ids of events already applied, and reject any event older
  than the step it would answer. Notifications, webhooks and message histories get replayed.
- **Use a transaction port** (`TransactionRunner`) for multi-repository decisions. Re-read the
  aggregate inside the transaction, so two competing decisions can't both apply.
- **Version references to mutable external objects.** For example, carry a notification's key *and*
  its post time, and refuse to act on a newer posting than the one that was classified.
- **Codecs treat stored text as hostile.** Strip separator characters before encoding, and skip
  unreadable records instead of throwing, so one bad row never breaks a screen.

Write down decisions and their rejected alternatives in `docs/architecture.md`. A "key decisions"
table is enough.

## 3. Build and code quality

Details are in [references/build.md](references/build.md). The essentials:

- Use Gradle with the Kotlin DSL and the wrapper. Every version goes in `gradle/libs.versions.toml`.
  Use the latest stable releases, and check that they exist before pinning them.
- All build policy lives in convention plugins in `<root>-build-logic` (an included build).
  Module build files only declare what is unique to them.
- The compiler is strict: warnings are errors, explicit API mode in library modules (Kotlin), and
  `-Werror` with `-Xlint:all` for Java.
- Linters run in `check` and fail the build:
  - Kotlin: ktlint (with Compose rules) and detekt.
  - Java: Spotless with Palantir or Google format, Checkstyle, Error Prone with NullAway.
  - Android: Lint with `warningsAsErrors`.
- One tool owns each concern (for example, line length belongs to the formatter, not the static analyser).
  Every suppression or exclusion carries a comment saying why.
- Public API is documented (KDoc/Javadoc). Library modules enforce this.
- Provide one aggregate task, `verifyAll`, that runs everything a change must pass except device tests.

## 4. Testing

Details are in [references/testing.md](references/testing.md). The essentials:

- Cover every layer with the right kind of test:
  - **Unit:** domain.
  - **Use case:** application, against fakes.
  - **Integration:** real storage, including migrations.
  - **Adapter:** real framework objects (Robolectric on Android).
  - **UI:** with accessibility checks on.
  - **UX journey:** across screens.
  - **End-to-end:** on a device or emulator.
  - **Architecture:** layering and naming rules.
  - **Performance:** a budget test plus a JMH benchmark.
  - **Mutation:** PIT.
- Quality gates fail the build:
  - Line coverage per module, set in the module (core ≥ 95%).
  - Mutation score per module (domain ≥ 85%).
  - A lower threshold is allowed only with a written reason, such as coroutine state-machine equivalent mutants.
- Classification-style logic gets a shared, realistic corpus of samples (anonymised real data
  plus synthetic coverage), with one expectation per sample, plus aggregate checks.
- **Device and destructive tests must never touch a personal device.** Target emulators
  explicitly (`ANDROID_SERIAL`), and make tests that change system settings refuse to run on real
  hardware.

## 5. Documentation and tooling

Every project has a `docs/` folder:

| Page | Covers |
|---|---|
| `README.md` | Index of the docs |
| `philosophy.md` | Problem, goal, principles in priority order, non-goals |
| `architecture.md` | Modules, dependency rule, ports, flows, key decisions |
| `testing.md` | Suite, how to run each kind, gates and their reasons |
| `development.md` | Toolchain, conventions, how to add things, release steps |
| `distribution.md` | Install, signing, publishing |
| `compatibility.md` | Supported platforms and versions |

Add domain-specific pages (for example privacy or protocol docs) as the project needs them.

- **Keep docs generic.** No personal devices, accounts, names or local paths. Real data used
  in tests or docs is anonymised: names, numbers, ZIP codes, and the paths of tracking links
  (which can identify the recipient). Never commit hashes of redacted values as a guard. Low-entropy
  values such as ZIP codes, phone numbers and first names can be recovered by brute force. Guard
  structurally instead, for example "every five-digit number is 00000".
- **Generate screenshots and animations from the real app with a script** (a scripted
  instrumented tour, plus an assembler that writes `docs/media/`). Regenerate them before each
  release. Never hand-edit them.
- **Ship an installer script for end users** in both bash and PowerShell. It:
  - asks before every step;
  - takes the same commands in both (install, update, setup, status, pair, uninstall);
  - supports `--yes`, `--dry-run` and device selection;
  - refuses to guess when several devices are connected;
  - answers "no" when there is no terminal;
  - fails with friendly errors that say what to check.
  Test it, don't just lint it: bats and Pester suites against a fake adb and a fake release
  server, on every OS and shell it claims to support, plus a run against the CI emulator
  (see [references/ci.md](references/ci.md)).

## 6. Continuous integration

Details are in [references/ci.md](references/ci.md). The essentials:

- CI runs **every** suite: build, lint, unit/integration/UI tests, mutation, performance, the
  emulator end-to-end matrix (minSdk, mid, targetSdk), and the installer tests. Each runs as its own
  parallel job, and a single aggregate `CI passed` job is the required check.
- Every job leaves evidence:
  - JUnit checks;
  - SARIF in code scanning, merged per tool;
  - coverage, mutation and benchmark tables in the job summary;
  - HTML/XML reports and checksummed binaries as artifacts.
- Cache hard with setup-gradle: the build cache, the configuration cache (with an encryption key),
  and AVD snapshots. Only the default branch writes the cache. Default to the MIT `basic` provider.
- Build Scans use the Develocity plugin in settings. They publish only from CI, only after the
  owner opts in to the terms with a repository variable, and with identifying data obfuscated.
- Never accept third-party terms, publish, or push on the user's behalf. Put each such choice behind
  a variable that the user sets.
- Lint the workflows with actionlint, and document every variable and secret in `docs/ci.md`.

## 7. Repository hygiene

- Keep build outputs, `local.properties`, keystores and JVM crash dumps (`hs_err_pid*.log`,
  `replay_pid*.log`) in `.gitignore`. Crash dumps contain local paths and environment details. If
  any were committed and the repository hasn't been pushed, purge them from history.
- Keep `.gitattributes` with LF endings for `*.sh`, `*.bats`, `*.py`, `gradlew` and extensionless
  launchers, and CRLF for `*.bat` and `*.cmd`. Commit
  scripts with the executable bit set.
- Commit in reviewable steps with conventional-commit messages. Never push or publish without the
  user's go-ahead.
