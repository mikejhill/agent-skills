# test-design

Language-agnostic rules for writing tests that catch real regressions and fail with clear messages: one behavior per test, specific assertions, isolation, test data builders, coverage targets, and a catalog of anti-patterns.

## Use

Loads automatically when the agent writes, reviews, or refactors tests. Examples:

- "Add tests for the discount calculator."
- "Review this test file for weak tests."

It pairs with the language skills, which supply the test runner and commands.

## Results

Tests follow Arrange-Act-Assert with descriptive names and diagnostic assertion messages. Coverage targets are 90%+ for core logic and 70%+ for CLI or UI orchestration.
