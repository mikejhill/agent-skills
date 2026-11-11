# Intent

**Maintain TypeScript engineering guidance with semantic parity to Python Development, adapted to TypeScript's ecosystem.** Keep the operational entry point short and use focused references for conditional detail.

## Goals and choices

| Python concept | TypeScript adaptation |
| --- | --- |
| Cohesive class-based modules | Class-first orchestration/state, readonly values, narrow injected contracts; pure parsers/transforms where conventional |
| src package layout | src/ per package, deliberate exports, no consumer imports of another package's source |
| Strict ty + ruff + poe | Strict tsc plus typed ESLint, separate formatter, package scripts and one non-mutating check task |
| uv runtime/environment/lock consistency | Runtime pin + exact packageManager + one lockfile + frozen install; preserve existing manager |
| Typed dataclasses at external boundaries | Decode unknown into readonly domain contracts; discriminated unions and useful generics |
| pytest behavior and edge checks | Vitest/default existing runner, deterministic fake I/O, negative type tests and packed consumers |
| Concise docstrings/comments | Concise public TSDoc, invariants/errors over signature restatement |
| Entry point, logging and error separation | Async application/CLI boundary, stdout data, stderr diagnostics, specific failure categories |

- Prefer pnpm for new package-managed projects, retaining npm/Yarn and supported module consumers in existing work.
- Prefer typed ESLint + Prettier for new comprehensive linting. Retain Biome as an intentional compatible profile; remove unsupported percentage/speed/equivalence claims.
- Pin a compatible compiler/linter combination rather than blindly installing every latest package. The validation baseline uses TypeScript 6.0.3 because the selected typescript-eslint 8.72.1 peer range is >=4.8.4 <6.1.0; the registry's newer compiler needs separate compatibility validation.
- Use tsc for ordinary unbundled Node builds, Vite/framework tooling for browser assets, and optional tsx development execution. Typecheck separately in every profile.
- Prefer Node ESM when compatible; preserve or deliberately test CommonJS/dual output. Runtime execution, declarations and package exports must agree.
- Avoid universal class wrappers, forced framework changes, arbitrary snippet caps, unchecked JSON casts, and scaffolds that imply unsupported runtime compatibility.
- Reuse project-setup/project-documentation/release guidance rather than copying generic workflows. Existing asynchronous mutation-main and threshold-alert policy remains authoritative; no new PR gate.

## Preservation

Original seven-file TypeScript skill captured in canonical Git commit `86382d6` before editing. Python skill and shared configuration are read-only inputs to this work. Generated harness copies are updated only by the coordinated scoped SkillSinc distribution.

## Validation record

Baseline environment: Windows, Node 24.7.0. Tools are installed only inside isolated fixtures with install scripts disabled; no global installation, credentials, network-policy changes, or real-project mutation.

- Skill frontmatter/schema and all relative reference links checked.
- Exact compiler/lint templates and complete source examples exercised in an isolated package: strict source/test typecheck, typed lint, formatter check, behavior tests, declaration build and emitted ESM loading.
- Independent forward tests cover an npm/CommonJS library, a compiled Node ESM CLI/service, and a two-package pnpm workspace; detailed outcomes and remaining platform limits are recorded in the task's validation report.
- Browser/framework, dual-output packaging, native type stripping, other OSes and additional supported runtimes are criteria-based profiles, not certified complete templates.

Consult current primary documentation linked in references before upgrading. Exact tool pins record tested compatibility, not a permanent recommendation to use an old patch.

## Log

- 2026-04-10: Initial Biome/tsx/use-case/CLI profiles and fnm runtime guidance.
- 2026-10-29: Review against actual Python skill; preserve original; add modular boundaries, comprehensive typing/typed lint, runtime/package discipline, compatible module profiles and isolated forward tests. Correct invalid Biome 2 keys, emitted extension examples, unsafe JSON casts and parser side effects.
