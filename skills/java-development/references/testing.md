# Testing conventions

## The pyramid

| Kind | Where | Runner | Purpose |
|---|---|---|---|
| Unit | `-core-domain` | JUnit 5/6 | Every value object, rule, policy and state transition |
| Corpus | domain tests reading `-core-corpus` | JUnit, parameterised | One expectation per realistic sample, plus aggregate checks (rates, documented exceptions, balance) |
| Use case | `-core-application` | JUnit plus Turbine (Kotlin Flow) | Use cases against in-memory ports, with whole-day scenario tests |
| Integration | `-data-*` | Robolectric (Android), Testcontainers (servers) | Real storage: round trips, conflicts, live queries, deletes |
| Migration | `-data-*` | Room `MigrationTestHelper` (driver API), Flyway or Liquibase tests | Every schema upgrade keeps data. Export schemas and commit them. |
| Adapter | `-platform-*` | Robolectric | Real framework objects; put the radio, clock or OS behind a small interface where the shadow can't emulate it |
| UI | `-feature-*` | Compose UI test on Robolectric, `enableAccessibilityChecks()` | Every state and interaction |
| UX journey | `-feature-*` | Compose UI test with the real view models and harness | A user flow across screens |
| End-to-end | `-app/src/androidTest` | Device or emulator | Real adapters, with only side effects such as SMS recorded |
| Architecture | `-architecture-tests` | Konsist (Kotlin) or ArchUnit (Java) | Layer dependencies, naming, port placement, module-to-package mapping |
| Performance | domain | `@Tag("performance")` budget test plus JMH | Latency budgets. Take the best of several batches so a busy machine doesn't fail them. |
| Mutation | pure modules | PIT | Tests notice wrong logic |

## Writing tests

- **Test behaviour through outcomes:** what was stored, sent or shown. Avoid checking which method ran.
- **Use fakes from `-core-testing`, not mocks.** A fake that behaves like the adapter survives refactoring.
- **Name tests as sentences.** JVM modules use backtick names in Kotlin, or `@DisplayName` or descriptive method names in Java. Android modules use JUnit 4 camelCase, because Robolectric requires JUnit 4.
- **Every misclassified real example becomes a corpus entry before the fix lands.**
- **Assertions that guard sensitive data compare hashes**, never the literal values.
- **Guard tests that could pass vacuously.** For example, assert that a source scan found more than N files.

## Gates (fail the build)

- **Line coverage** per module, from Kover (Kotlin) or JaCoCo (Java). Exclude generated code: Room `_Impl`, Compose singletons, previews, benchmarks.
- **Mutation score** per module. Exclude performance tests from PIT, and `avoidCallsTo` Kotlin intrinsics, `kotlin.ResultKt` and coroutine internals.
- **Lower thresholds need a reason.** For example, suspend functions compile to state machines that yield equivalent mutants; review the survivors and write the reason next to the threshold.

## Running tests safely

- **Cap parallel forks.** Robolectric JVMs are large; one fork per Android module is enough, because modules already run in parallel. Uncapped forks on a many-core machine can exhaust memory and crash test JVMs.
- **Device tasks run on every connected device by default.** Target an emulator explicitly with `ANDROID_SERIAL=emulator-5554`, and say so in the docs.
- **Destructive device tests refuse to run on real hardware.** This covers tests that toggle dark mode, demo mode, snooze notifications or grant permissions; check `ro.kernel.qemu`. Restore the state they change, and use an in-memory database and recorded side effects.
- **Runner arguments exclude opt-in suites** such as a media-capture tour (`notClass=…`), so normal runs never report them as skipped or failed. A dedicated task sets `class=…` instead.
- **Collect device output with TestStorage**, using `useTestStorageService=true` and `androidTestUtil(test-services)`. AGP then pulls it into `build/outputs/connected_android_test_additional_output/`.

## Corpus guidance

- **Mix real and synthetic samples.** Real samples are anonymised: names replaced, ZIP codes zeroed, area codes replaced by an unassigned one, with structure such as neighbouring numbers kept. Synthetic samples cover sources the real ones lack, and use fictional people and organisations for anything that will be published.
- **Each sample records its category, expected result and origin**, plus a note whenever the expectation isn't the obvious one, such as a known trade-off.
