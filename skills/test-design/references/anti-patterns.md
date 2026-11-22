# Test anti-patterns

Each of these gives false confidence. Fix or delete on sight.

| Anti-Pattern              | Description                                                                                        | Fix                                                                                 |
| ------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **The No-Op**             | Test body is empty or contains no assertions.                                                      | Add meaningful assertions or delete the test.                                       |
| **The Tautology**         | Asserts that a value equals itself or that a mock returns its configured value.                     | Assert against production code output, not test setup.                              |
| **The Giant**             | Single test verifies 10+ unrelated behaviors.                                                      | Split into one test per behavior.                                                   |
| **The Clone**             | Two tests cover the same code path with inputs from the same equivalence class.                    | Delete the duplicate.                                                               |
| **The Inspector**         | Asserts on internal implementation details (private state, call order of non-critical methods).     | Assert on observable output or public state only.                                   |
| **The Silent Catcher**    | Wraps code in try/catch and asserts nothing in the catch block, or asserts `true` unconditionally.  | Let exceptions propagate. Assert on specific error type/message.                    |
| **The Flake**             | Depends on timing, random data, or external service availability without controlled substitutes.   | Inject deterministic clocks, seeded randomness, or fakes.                           |
| **The Free Rider**        | Relies on side effects from a previous test. Passes in suite, fails in isolation.                  | Make the test self-contained with its own setup.                                    |
| **The Framework Tester**  | Verifies language/framework behavior rather than production code.                                  | Delete — framework correctness is not your responsibility.                          |
| **The Shallow Check**     | Uses only truthiness assertions (`assertNotNull`, `assertTrue`) when exact values are available.    | Replace with exact-value assertions.                                                |
| **The Mirror**            | Re-implements production logic in the test to compute the expected value.                          | Use hardcoded expected values derived from requirements, not code.                  |
| **The Optimist**          | Tests only the happy path. No error, boundary, or edge-case coverage.                              | Add negative, boundary, and error-path tests.                                       |
| **The Commentator**       | Assertions are commented out or wrapped in conditionals that never execute.                         | Uncomment or remove dead assertions.                                                |
| **The Log Reader**        | Verifies behavior by parsing log output instead of asserting on return values or state.            | Assert on observable outputs. Use logs only when they are the documented interface.  |
| **The Fabricator**        | Uses invented field names or constructor arguments not present in production code.                  | Read the production type definition. Use exact field names. Run tests to verify.    |
| **The Timezone Trap**     | Uses date/time values near midnight UTC boundaries where timezone offsets shift the date.           | Use mid-day or mid-year values to avoid ambiguity. Test timezone boundaries explicitly when relevant. |
| **The Orphan Mock**       | Mocks a framework module but misses imports used by transitive dependencies — test fails at import. | Enumerate all imports across the entire package. Mock every module and attribute.   |
