---
name: test-design
description: >-
  Language-agnostic test design: one behavior per test, naming, assertions with
  diagnostics, isolation, test data, coverage, and anti-patterns. Use when
  writing, reviewing, or refactoring unit, integration, or end-to-end tests.
  Not for test runner or CI setup.
---

# Test design

Write tests that each prove one behavior and, on failure, say exactly what broke. Language skills (such as `python-development`) supply frameworks and commands. This skill supplies the design rules.

## Workflow

1. **Read the production code first.** Record the exact signatures, field names, nested keys, and constructor arguments. A test that fails with `unexpected keyword argument` is a defect in the test.
2. **Measure a baseline** when coverage tooling exists, and list the gaps ([coverage.md](references/coverage.md)).
3. **List equivalence classes** per input: typical valid, boundary, and invalid. Plan one test per class per code path.
4. **Write each test** as Arrange, Act, Assert, with exactly one action under test.
5. **Check the test can fail**: picture a wrong implementation and confirm the assertion catches it.
6. **Run the suite**, in isolation and in random order when the runner supports it. Re-measure coverage.
7. **Scan for anti-patterns** ([anti-patterns.md](references/anti-patterns.md)) and fix or delete matches.

## Rules

**Design**

- One logical behavior per test. Several assertions are fine only when they check facets of one outcome, such as the status and body of one response.
- Tests are independent and deterministic. Inject clocks, seed randomness, and fake external services.
- Every test calls production code and has an assertion that can fail.
- Clean up everything a test creates: files, handles, globals, and environment variables.
- Never compute expected values with the production algorithm. Derive them from requirements.
- No environment-specific values (absolute paths, hostnames, ports) in tests.
- Never catch and swallow exceptions to make a test pass.
- Do not test the language, the framework, or a mock's configured return value.

**Naming**

- The name states the unit, the scenario, and the expected result: `withdraw_oneAboveBalance_returnsInsufficientFunds`, or the runner's natural-language form. Never `test1` or `happyPath`.
- Suites are named after the unit under test.

**Assertions**

- Use the most specific assertion: exact values over truthiness, specific error types over "it failed".
- Give each assertion a message with what was tested, the expected value, and the actual value, so the failure is clear without opening the test.
- Assert on observable behavior, not internals such as private state or call counts on non-critical collaborators.

**Isolation**

- Unit tests replace databases, networks, file systems, and clocks with stubs, fakes, or in-memory versions.
- Prefer per-test setup to shared mutable fixtures.
- Keep integration tests separable from unit tests by directory or naming, and document their external dependencies.
- For code that imports a framework that is not installed, read [isolation.md](references/isolation.md).

**Test data**

- Use builder or factory functions with valid defaults and keyword overrides for any complex object used by three or more tests. Tests override only the fields they care about.
- Use synthetic data for unit tests. Use real sample files only for end-to-end parsing tests, as a complement.

**Coverage**

- Every public interface gets a success test and one test per documented error.
- Test boundaries explicitly: zero, one, min, max, empty, null, and off-by-one.
- Negative tests assert the documented error, not just "no crash".
- Targets: 90%+ lines for core logic, 70%+ for CLI or UI orchestration. A number alone is not a pass; shallow assertions at 95% are worse than rigorous ones at 80%.

**Regressions**

- For each fixed bug, add a test that reproduces the original failure, named for the behavior, asserting the specific wrong result. Keep it unless the behavior is removed on purpose.

**Organization**

- One test file per module, named by the language's convention (`test_<module>.py`, `<module>.test.ts`).
- Put helpers and builders at the top of the file or in a shared module (`conftest.py`, `testutils`).

## References

- [anti-patterns.md](references/anti-patterns.md): read when reviewing tests or before declaring new tests done.
- [coverage.md](references/coverage.md): read when measuring coverage or analyzing gaps across a codebase.
- [isolation.md](references/isolation.md): read when the code under test imports a framework missing from the test environment.
- [examples.md](references/examples.md): read for worked examples of builders, boundary sets, and regression tests.
