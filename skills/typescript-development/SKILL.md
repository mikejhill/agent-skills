---
name: typescript-development
description: Create, modify, refactor, or review TypeScript snippets, scripts, libraries, browser applications, Node.js services, and CLIs. Use for modular class-first design, strict boundary-safe typing, linting, testing, and portable package/runtime configuration.
---

# TypeScript Development

**Deliver cohesive modules, explicit contracts, and reproducible checks.** Preserve the repository's supported consumers and established tooling; use the defaults below for new work.

## Select scope

| Mode | Use when | Deliver |
| --- | --- | --- |
| OneOff | Inline answer or quick expression | Short typed snippet, no scaffold |
| Script | Reusable single-file utility | Checked script and pinned repository-local dependencies when needed |
| FullProject | Library, application, CLI, or multiple modules | Source in `src/`, tests, package metadata, lockfile, runnable checks |

Infer the smallest sufficient mode and target: Library, Browser, Service, or CLI. Inspect existing scripts, lockfile, runtime support, module format, framework, and public API before changing configuration. A narrow edit does not authorize a toolchain migration.

## Core rules

**Design**

- Strongly prefer classes for stateful services and application orchestration; use readonly value objects and narrow injected interfaces. Pure functions are appropriate for stateless transformations, parsers, and framework callbacks. Avoid artificial utility classes.
- Group by cohesive domain or feature. Keep domain logic independent of transport, filesystem, CLI, and framework adapters; wire implementations at the entry point. Prefer composition over inheritance.
- Keep imports free of startup, network, and filesystem side effects. No shared module-level mutable state. Use early guards and shallow control flow; split a method before nesting exceeds three levels.
- Validate external data once at each trust boundary, then enforce domain invariants where they belong. Keep parsing, I/O, and business logic separate.

**Types**

- Enable `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, and `noFallthroughCasesInSwitch` for new projects. Check tests and configuration as well as source.
- Annotate public signatures and non-contextual parameters/returns; allow clear local inference and contextually typed callbacks. Prefer readonly data, discriminated unions with exhaustive handling, and generics that preserve real relationships.
- Receive JSON, environment, user input, and untyped dependencies as `unknown`; validate to domain types. A generic `fetch<T>`, assertion, or `satisfies` does not validate runtime data.
- Avoid `any`, unsafe assertions, and non-null assertions. Isolate unavoidable external unsafety behind a typed adapter with a reason and tests. Use described `@ts-expect-error` only for a specific known diagnostic or a negative type test; never blanket-disable checks.
- Prefer string unions or `as const` objects over new enums. Prefer named exports, type-only imports, and explicit public exports; preserve framework-required defaults and existing compatible API forms.

**Tooling and portability**

- New package-managed projects: prefer pnpm with an exact `packageManager` version and committed `pnpm-lock.yaml`; preserve npm/Yarn in existing repositories. Pin the development runtime separately from the supported `engines` range.
- New comprehensive lint profile: ESLint flat config + typescript-eslint typed rules; Prettier owns formatting, `tsc` owns type checking. Preserve a working Biome profile when its rules meet the project requirements; do not claim that the compiler fills every typed-lint gap.
- Keep lint, format checking, type checking, tests, and build independently runnable. Expose one non-mutating `check` task. Fix commands are separate; never weaken checks to obtain a pass.
- Default builds: Vite for bundled browser applications; `tsc` for ordinary Node.js libraries/services/CLIs. Use tsx only when useful for development. These runners/bundlers do not replace type checking.
- Choose module format, resolution, extensions, runtime APIs, and output target together. Prefer ESM for new compatible projects; retain or explicitly design CommonJS/dual support when consumers require it. See [profiles](references/modes.md).
- Use local tools and cross-platform scripts. Review lifecycle scripts and dependency-build permissions for the selected manager version; do not silently enable all scripts, install global tools, or add credentials/network permissions.

**Behavior and documentation**

- Use conventional naming: kebab-case files, PascalCase types/classes, camelCase members; keep framework conventions. Document public contracts with concise TSDoc, especially invariants, failure modes, units, and side effects.
- Catch as `unknown`, narrow deliberately, preserve causes, and use specific application error categories when callers need to distinguish them. Never silently suppress errors.
- Separate machine output (stdout) from diagnostics (stderr); use an injected structured logger for services. Configure logging once and redact secrets.
- Test public behavior, invalid inputs, and boundaries; inject fake I/O and use temporary directories. Test the built artifact and package exports, not only development execution.

## Work and verify

1. Select mode/profile; inspect compatibility and read only the relevant references.
2. Implement a cohesive vertical slice, including validation and behavior tests.
3. Run frozen install when a lockfile already exists, then typecheck, lint, format check, tests, and build using the project's scripts.
4. Exercise emitted code or packed consumers on the advertised runtime/module formats. Report exact commands and failures/unverified platforms; do not equate transpilation with successful checks.
5. Follow the repository's existing asynchronous mutation-main/release policy with threshold alerts. These quality checks do not establish a new PR gate or authorize publication.

## References

| Read | When |
| --- | --- |
| [modes.md](references/modes.md) | Runtime, package management, module format, browser, workspace, or library decisions |
| [standards.md](references/standards.md) | Module boundaries, naming, typing, errors, documentation, and tests |
| [templates.md](references/templates.md) | New strict Node.js compiler/linter/task configuration and profile adaptations |
| [cli-patterns.md](references/cli-patterns.md) | Testable parsing, asynchronous entry points, CLI streams and exit codes |
| [examples.md](references/examples.md) | Validated boundary decoder, generic API, and refactoring examples |

Generic project setup, documentation structure, and release workflows belong to their existing skills; this skill owns TypeScript-specific decisions.
