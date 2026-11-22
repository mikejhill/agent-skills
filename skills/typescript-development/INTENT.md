# Intent

Maintain TypeScript engineering guidance with semantic parity to `python-development`, adapted to TypeScript's ecosystem. Keep the entry point short and put conditional detail in focused references.

## Goals

1. Parity with `python-development`: each Python concept has a TypeScript adaptation (table below).
2. New work gets strict, reproducible defaults; existing repositories keep their working tooling and supported consumers.
3. Every template and example is verified in an isolated fixture before it ships.

| Python concept | TypeScript adaptation |
| --- | --- |
| Cohesive class-based modules | Class-first orchestration and state, readonly values, narrow injected contracts; pure parsers and transforms where conventional |
| `src` package layout | `src/` per package, deliberate exports, no consumer imports of another package's source |
| Strict ty + ruff + poe | Strict `tsc` plus typed ESLint, a separate formatter, package scripts, and one non-mutating check task |
| uv runtime, environment, and lock consistency | Runtime pin + exact `packageManager` + one lockfile + frozen install; preserve the existing manager |
| Typed dataclasses at external boundaries | Decode `unknown` into readonly domain contracts; discriminated unions and useful generics |
| pytest behaviour and edge checks | Vitest or the existing runner, deterministic fake I/O, negative type tests, and packed consumers |
| Concise docstrings and comments | Concise public TSDoc, invariants and errors over signature restatement |
| Entry point, logging, and error separation | Async application or CLI boundary, stdout data, stderr diagnostics, specific failure categories |

## Requirements

- Prefer pnpm for new package-managed projects; retain npm or Yarn and supported module consumers in existing work.
- Prefer typed ESLint + Prettier for new comprehensive linting. Retain Biome as an intentional compatible profile. No unsupported percentage, speed, or equivalence claims.
- Pin a compatible compiler and linter combination rather than installing every latest package.
- `tsc` for ordinary unbundled Node builds, Vite or framework tooling for browser assets, optional tsx for development. Typecheck separately in every profile.
- Prefer Node ESM when compatible; preserve or deliberately test CommonJS or dual output. Runtime execution, declarations, and package exports must agree.
- Avoid universal class wrappers, forced framework changes, arbitrary snippet caps, unchecked JSON casts, and scaffolds that imply unsupported runtime compatibility.
- Reuse project-setup, documentation, and release guidance rather than copying generic workflows. The existing asynchronous mutation-testing and threshold-alert policy stays authoritative; no new PR gate.
- Validate templates only inside isolated fixtures with install scripts disabled: no global installs, credentials, network-policy changes, or real-project changes.

## Log

- 2026-04-10: Initial Biome, tsx, use-case, and CLI profiles, with fnm runtime guidance.
- 2026-10-29: Reviewed against the Python skill. Original seven-file skill preserved in commit `86382d6` before editing. Added modular boundaries, comprehensive typing and typed lint, runtime and package discipline, compatible module profiles, and isolated forward tests. Corrected invalid Biome 2 keys, emitted-extension examples, unsafe JSON casts, and parser side effects.
- 2026-10-29: [agent] Validation baseline: Windows, Node 24.7.0. TypeScript 6.0.3, because typescript-eslint 8.72.1 requires `>=4.8.4 <6.1.0`. Templates and examples passed strict source and test typecheck, typed lint, format check, behaviour tests, declaration build, and emitted ESM loading. Forward tests covered an npm CommonJS library, a compiled Node ESM CLI or service, and a two-package pnpm workspace. Browser and framework, dual-output packaging, native type stripping, other OSes, and other runtimes are criteria-based profiles, not certified templates. Exact pins record tested compatibility, not a permanent recommendation.
- 2026-11-22: [agent] Migrated to the `skill-development` standard: INTENT restructured into Goals, Requirements, and Log without changing content; shorter description; README added.
