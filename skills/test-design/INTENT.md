# Intent

Make agents write tests that prove one behavior each, fail with a message that pinpoints the defect, and together cover the code without redundancy or false confidence. Renamed from `testing-standards`.

## Goals

1. Tests are correct on first run: field names, signatures, and constructor arguments match the production code.
2. Every test can fail and, when it does, explains the defect without opening the test source.
3. The suite covers success, error, and boundary paths by risk, without duplicate tests.
4. False-confidence tests (no-ops, tautologies, mirrors, flaky tests) are caught and removed.

## Requirements

- Language-agnostic: test design, naming, assertions, isolation, coverage strategy, failure diagnostics, and anti-pattern elimination for unit, integration, end-to-end, and acceptance tests.
- Out of scope: language-specific framework configuration, test runner setup, and CI pipeline design.
- Inspect production code signatures before writing test data. Never invent field names.
- Coverage targets: 90%+ lines for core library code, 70%+ for CLI or UI orchestration code. Coverage percentage alone is not a pass condition.
- Builders or factories for complex test data. Regression tests for every fixed bug.
- Module stubbing for code that depends on frameworks unavailable in the test environment.

## Log

- 2026-11-10: Imported into the SkillSinc library layout as `testing-standards`. Requirements above are taken from that skill.
- 2026-11-22: [agent] Renamed to `test-design` during the migration to the `skill-development` standard ("testing" is a gerund). Rewrote `SKILL.md` from 414 to about 100 lines: dropped the persona, the MUST/MUST NOT lists, and the validation section that repeated the rules. The anti-pattern catalog, coverage workflow, framework stubbing, and examples moved to `references/`.
- 2026-11-22: [agent] Removed named references to other skills and instruction files; adjacent concerns are now described by capability ("any ... standards the user has") so the skill stands alone.
