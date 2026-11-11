# Build conventions

## Layout

```
<root>/
├── settings.gradle.kts           includeBuild("<root>-build-logic"); include(":<root>-…") per module
├── build.gradle.kts              plugins { … apply false }, plus aggregate tasks (verifyAll, …)
├── gradle.properties             parallel, build cache, configuration cache on
├── gradle/libs.versions.toml     every version, library, plugin, and the convention plugin ids
├── gradle/gradle-daemon-jvm.properties   toolchainVersion=21: the build picks its own JDK
├── <root>-build-logic/           included build, single project, package …<root>.build.logic
├── config/detekt/detekt.yml      (Kotlin) only deliberate deviations, each commented
├── .editorconfig                 formatter settings (ktlint reads it)
└── <root>-<layer>-<name>/        one directory per module, flat
```

Turn on `enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")` and set
`repositoriesMode = FAIL_ON_PROJECT_REPOS`.

## Convention plugins

These are class-based plugins in `<root>-build-logic`. The plugin libraries are `compileOnly`
there and declared `apply false` in the root build, so their versions resolve once. Use one plugin per
module kind:

| Plugin | Applies |
|---|---|
| `<root>.jvm.library` | Kotlin/Java JVM, toolchain from the catalog, strict compiler, JUnit Platform, quality and coverage, a `performanceTest` task for `@Tag("performance")` tests (excluded from `test`) |
| `<root>.android.library` / `.android.application` | AGP, compile/min/target SDK from the catalog, strict Lint, Robolectric test dependencies, capped test forks |
| `<root>.android.compose` | Compose compiler, the BOM, and UI-test dependencies, including the accessibility checks artifact |
| `<root>.mutation` | PIT, with per-module thresholds |

Expose per-module settings through a small extension, for example
`<root> { minimumLineCoverage.set(95); minimumMutationScore.set(85) }`, with conventions as defaults.

## Compiler strictness

- **Kotlin:**
  - `allWarningsAsErrors`, `progressiveMode`, and `-Xjsr305=strict`.
  - `-Xexplicit-api=strict` for library main source sets, but not tests or the app.
- **Java:** `options.compilerArgs += ["-Xlint:all", "-Werror", "-parameters"]`, plus Error Prone and
  NullAway (`NullAway:AnnotatedPackages=<root package>`).
- Keep the target JVM bytecode level in the catalog and use the same value everywhere.

## Linters

| Concern | Kotlin | Java |
|---|---|---|
| Formatting | ktlint via `org.jlleitschuh.gradle.ktlint`, `ktlint_official` style, Compose rules | Spotless (Palantir or Google Java Format) |
| Static analysis | detekt, `buildUponDefaultConfig` | Error Prone, SpotBugs |
| Style and structure | detekt | Checkstyle |
| Android | Lint: `warningsAsErrors`, `abortOnError`, `checkDependencies`. Disable only date-dependent checks (newer versions available, old target API). | same |

Rules of thumb:

- **One tool owns each concern.** Turn off duplicates, for example detekt's `MaxLineLength` when ktlint owns line length.
- **Exclusions carry a comment** stating the reason, such as "Composables are PascalCase" or "enum entries name their constants".
- **Data files may relax line length** in `.editorconfig` for their module only. Corpora read better one message per line.
- **Script linters run in CI too:** shellcheck for bash, and PSScriptAnalyzer with a commented settings file for PowerShell.

## Privacy and manifest guarantees (apps)

Guarantees that matter to users get a test. For example, assert the merged manifest requests no
`INTERNET` permission, and use `tools:node="remove"` so a library can't merge it back in.

## Versions

Pick the latest stable release of each tool and confirm it exists in its repository's metadata
before pinning it. When two tools don't get along, fix it with the smallest local change and a
comment. One example was upgrading Espresso because the Compose test idling resource called a
removed API.

## Releases

- Signing comes from an ignored `keystore.properties` locally, or environment variables in CI. Without either,
  release builds are left unsigned.
- A tag-triggered workflow verifies, builds, signs, checksums and attaches the artifacts. It also
  regenerates the documentation media.
- `prepareRelease` runs `verifyAll` and then regenerates the media.
