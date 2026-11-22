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

## Preservation

Original seven-file TypeScript skill captured in canonical Git commit `86382d6` before editing. Python skill and shared configuration are read-only inputs to this work. Generated harness copies are updated only by the coordinated scoped SkillSinc distribution.

## Validation record

Baseline environment: Windows, Node 24.7.0. TypeScript is pinned to 6.0.3 because typescript-eslint 8.72.1 requires `>=4.8.4 <6.1.0`. Tools are installed only inside isolated fixtures with install scripts disabled; no global installation, credentials, network-policy changes, or real-project mutation.

- Skill frontmatter/schema and all relative reference links checked.
- Exact compiler/lint templates and complete source examples exercised in an isolated package: strict source/test typecheck, typed lint, formatter check, behavior tests, declaration build and emitted ESM loading.
- Independent forward tests cover an npm/CommonJS library, a compiled Node ESM CLI/service, and a two-package pnpm workspace; detailed outcomes and remaining platform limits are recorded in the task's validation report.
- Browser/framework, dual-output packaging, native type stripping, other OSes and additional supported runtimes are criteria-based profiles, not certified complete templates.

Consult current primary documentation linked in references before upgrading. Exact tool pins record tested compatibility, not a permanent recommendation to use an old patch.

## Log

- 2026-04-10: Initial Biome/tsx/use-case/CLI profiles and fnm runtime guidance.
- 2026-10-29: Review against actual Python skill; preserve original; add modular boundaries, comprehensive typing/typed lint, runtime/package discipline, compatible module profiles and isolated forward tests. Correct invalid Biome 2 keys, emitted extension examples, unsafe JSON casts and parser side effects.
- 2026-11-22: [agent] Migrated to the `skill-development` standard: Goals and Requirements sections added from the existing content; shorter description; README added. Preservation, validation record, and log entries kept verbatim.
- 2026-11-22: [agent] Restored the TypeScript 6.0.3 pin rationale (typescript-eslint 8.72.1 requires `>=4.8.4 <6.1.0`) to the validation record; it had existed only in a reconstructed log entry.
- 2026-11-22: [agent] Removed named references to other skills and instruction files; adjacent concerns are now described by capability ("any ... standards the user has") so the skill stands alone.
