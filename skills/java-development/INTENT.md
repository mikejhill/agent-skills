# Intent

Capture how JVM projects are structured and held to account, from building a production Android app end to end, so new Java, Kotlin, and Android projects start with the same conventions.

## Goals

1. A module or package name tells you where code lives without opening a build file.
2. Business rules are testable without any framework.
3. CI runs every suite and leaves evidence, so "done" means proven.
4. Nothing personal leaks, and nothing is published or accepted on the user's behalf.

## Requirements

- Gradle with the Kotlin DSL, version catalog, and convention plugins in an included build.
- Module and package naming derived from the root project name, flat directories, no overlapping packages, enforced by an architecture test.
- Layered domain-driven architecture (ports and adapters), with in-memory fakes instead of mocking frameworks.
- Strict compilers and linters that fail the build.
- The full test pyramid: unit, integration, UI, end-to-end, architecture, performance, and mutation, with coverage and mutation gates.
- Comprehensive GitHub Actions CI: caching, Build Scans behind an owner opt-in, SARIF, artifacts, and summaries.
- Documentation in `docs/`, generated screenshots, and release and install tooling with tested installer scripts in Bash and PowerShell.
- Device and destructive tests never touch a personal device.
- Applies to plain Java and Kotlin libraries and services as well as Android.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. Description cut from 775 to about 290 characters. Architecture detail and documentation and installer guidance moved from `SKILL.md` to `references/architecture.md` and `references/docs-and-tooling.md`.
