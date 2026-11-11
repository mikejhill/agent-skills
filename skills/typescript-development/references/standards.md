# TypeScript code standards

## Cohesion and dependency direction

- Organize by feature/domain once the project grows; keep a small library flat under `src/`. No empty service/model/util folders.
- A module owns one coherent responsibility, not necessarily exactly one symbol. Keep private helpers/types near their consumer; split when a responsibility or dependency direction changes.
- Domain models and policies depend on narrow contracts, not concrete HTTP/DB/filesystem implementations. Application services coordinate domain work; adapters translate external data. Bootstrap alone wires concrete implementations.
- Strongly prefer service classes for state, lifecycle, and orchestration. Inject collaborators through constructors; use `private readonly` or `#private` for internals. Use plain readonly objects for values and pure functions for stateless behavior.
- Prefer composition; introduce abstract base classes only for a real shared invariant/implementation. Do not create an interface for every class automatically.
- No circular imports, global mutable registries, broad catch-all `utils.ts/types.ts`, or barrels that pull runtime adapters into the domain. A package's index is an intentional public surface.
- Prefer early returns, small methods, and at most three nesting levels. Decompose by responsibility rather than line count.

## Naming and API

| Item | Default |
| --- | --- |
| Files/directories/package names | kebab-case; npm scope when appropriate |
| Classes, interfaces, type aliases | PascalCase; no interface `I` prefix |
| Functions, methods, properties | camelCase; meaningful domain verbs/nouns |
| Boolean state | is/has/can where descriptive |
| Stable module constants | UPPER_SNAKE_CASE; ordinary readonly values may use camelCase |
| Private members | private or #private; no automatic underscore prefix |
| Tests | `*.test.ts` near source or mirrored under `tests/` |

Honor framework conventions (e.g. PascalCase components, route filenames and required default exports). Prefer named exports for application/library APIs and `import type` for erased types. Avoid exporting internal adapters or publishing every source path. Public API/serialized field renames require compatibility consideration.

## Comprehensive typing

- Use the strict compiler baseline in [templates](templates.md). `strict` alone does not enable every useful check.
- Explicit public parameter/return types keep API intent stable. Inference is useful for literals, locals, and contextual callbacks; do not erase it with redundant annotations or broad `Record<string, unknown>` return contracts.
- Use `readonly` properties/arrays for input/value contracts; it is compile-time shallow protection, not deep runtime immutability.
- Model valid states with discriminated unions; narrow before accessing members, and exhaust switches with `never`. Prefer optional absence to present `undefined` when exactOptionalPropertyTypes is enabled.
- Use generics only for a relationship between values/types (e.g. input to output), with constraints when needed. A generic used only in a return type cannot validate incoming JSON.
- Use `satisfies` for assignability without discarding inference, `as const` for literal sets, and unions instead of new enums unless runtime interop requires one.
- Decode `unknown` at JSON/API/storage/env/CLI boundaries. Check shape AND semantic invariants (finite numbers, allowed values, bounds). Use a small decoder for simple data; choose an existing schema validator or Zod/Valibot when schemas/composition justify a dependency.
- Assertions, branding, `satisfies`, and generic annotations are not validation. Avoid `as T`, `!`, and leaking `any`; wrap unavoidable third-party unsafety, explain it, and test the adapter.
- Narrow caught values as `unknown`. A descriptive, narrowly targeted `@ts-expect-error` is suitable for negative compile tests; never use `@ts-ignore` to hide unexplored errors.

## Lint, formatting, and compiler roles

| Check | Owns |
| --- | --- |
| tsc | Static type correctness, module resolution, declaration emission |
| Typed ESLint | Promise handling, unsafe flows, exhaustiveness, code policy using type information |
| Prettier or Biome formatter | Deterministic layout |
| Tests/runtime smoke | Observable behavior and actual module/package loading |

New strict projects use typescript-eslint `strictTypeChecked` with projectService; review its evolving rules on upgrades and pin versions. Fail lint warnings via `--max-warnings 0`. Avoid the blanket “all rules” approach: deprecated, conflicting, stylistic, or framework-incompatible rules do not increase correctness.

Biome remains a valid intentional profile for its supported coverage and speed. Verify required promise/unsafe-flow checks against the installed version; choose typed ESLint when missing rules matter. Do not run two competing formatters or duplicate the same lint domains without a specific reason. Add framework/a11y plugins only for the relevant target.

## Errors, logging, and comments

- Use specific error classes or typed results where callers distinguish recoverable outcomes. Keep a small AppError hierarchy for applications, not a bespoke hierarchy for every tiny function.
- Preserve root causes with ErrorOptions. Narrow at handling boundaries; log once where an error is actually handled, not repeatedly at each rethrow. Validate preconditions without repeating every trusted internal shape check.
- Service logging is structured with context (e.g. existing logger or pino); inject it and redact secrets. CLI diagnostics go to stderr; browser logging follows the app's production policy.
- Give modules a brief purpose comment when not obvious; concise TSDoc for public classes, methods, interfaces and functions. Add @param/@returns only for information beyond types; @throws for meaningful failure conditions.
- Short logical block comments may help long methods; inline comments explain surprising behavior/workarounds. Avoid restating code or generating empty documentation boilerplate.

## Tests

- Test public contracts: success, invalid input, failures and edge cases. Group by behavior/class; use table-driven tests for repeated cases (typically 3+).
- Vitest is the new-project default when its ecosystem is useful; preserve a working runner, and use node:test for lean Node-only packages when sufficient. No jsdom dependency unless DOM behavior needs it.
- Inject fake network/clock/process boundaries; use temporary files and deterministic timers. Restore mocks and close handles after tests; no real network or arbitrary sleeps.
- Include async rejection paths, cancellation/cleanup for long-running services, and compile-time negative/consumer tests for public generic APIs.
- Coverage identifies missing behavior; honor existing thresholds and alert policy. Do not create a new PR gate or hide files simply to improve the percentage.
- Run the built application/package as well as source-level tests. A successful tsx/Vitest run can conceal emitted path, bin, export, or declaration failures.

Sources: [typed linting](https://typescript-eslint.io/getting-started/typed-linting/), [shared config stability](https://typescript-eslint.io/users/configs/), [ESLint flat config](https://eslint.org/docs/latest/use/configure/configuration-files), [Biome linter](https://biomejs.dev/linter/), [Vitest](https://vitest.dev/guide/).
