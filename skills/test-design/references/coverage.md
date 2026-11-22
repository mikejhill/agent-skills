# Coverage measurement and gap analysis

## Measure

1. Run the suite with coverage before writing tests, to get a baseline.
2. Classify uncovered lines: business logic, error handling, framework orchestration, or dead code.
3. Cover business logic and error handling first. They carry the most regression risk.
4. Re-measure after each batch and confirm the new tests hit the intended lines.
5. Document lines excluded on purpose (framework glue, platform-specific code) with a one-line reason.
6. Flag dead or unreachable code for removal instead of testing it.

## Targets

| Code | Line coverage |
| --- | --- |
| Core logic: business rules, parsers, models, utilities | 90%+ |
| CLI or UI orchestration, through mocked integration tests | 70%+ |
| Glue for a framework that is unavailable in tests | Lower is acceptable. Extract and test all pure logic. |

## Gap analysis

For every public function, method, class, and module, check:

- A success-path test with representative input.
- A test for each documented error or exception.
- Boundary tests for numeric, string, and collection parameters.
- Optional parameters tested both given and omitted.
- The return type and structure match the documented contract.

A public interface with no tests is a gap. Prioritize: error handling, then data transformation, then accessors, then display formatting.
