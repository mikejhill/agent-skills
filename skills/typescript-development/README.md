# typescript-development

TypeScript standards for snippets, scripts, libraries, browser apps, Node.js services, and CLIs. It mirrors `python-development`: cohesive class-first modules, strict types validated at boundaries, and one reproducible check task.

## Use

Loads automatically when the agent writes, refactors, or reviews TypeScript. Examples:

- "Create a small Node CLI that converts CSV to JSON."
- "Review the typing in src/api."

In existing repositories the agent keeps the current package manager, linter, and module format unless you ask for a migration.

## Requirements

- Node.js and the project's package manager. New projects default to pnpm, ESLint with typescript-eslint, Prettier, and Vitest, installed locally per project.

## Results

New projects get `src/` and tests, a lockfile, strict `tsconfig`, and a non-mutating `check` script covering typecheck, lint, format, tests, and build.
