# Node.js CLI patterns

**Keep startup thin and parsing testable.** Bootstrap wires dependencies; parsing handles syntax; domain services enforce invariants; adapters own I/O.

## Parse without exiting or writing

For a small CLI, use `node:util` parseArgs; keep an established Commander/yargs setup when its subcommands/help justify it. Receive argv explicitly, not from process globals. Return a discriminated command; help/version are commands too.

```typescript
import { parseArgs } from "node:util";

export type Command =
  | { readonly kind: "help" }
  | { readonly kind: "version" }
  | {
      readonly kind: "run";
      readonly inputPath: string;
      readonly format: "json" | "text";
    };

export function parseCli(argv: readonly string[]): Command {
  const { values } = parseArgs({
    args: [...argv],
    strict: true,
    options: {
      help: { type: "boolean", short: "h" },
      version: { type: "boolean" },
      input: { type: "string", short: "i" },
      format: { type: "string", default: "json" },
    },
  });

  if (values.help === true) return { kind: "help" };
  if (values.version === true) return { kind: "version" };
  if (values.input === undefined || values.input.trim() === "") {
    throw new TypeError("--input is required");
  }
  if (values.format !== "json" && values.format !== "text") {
    throw new TypeError("--format must be json or text");
  }
  return {
    kind: "run",
    inputPath: values.input,
    format: values.format,
  };
}
```

A larger application should translate parser errors to its specific user-input error category. Domain validation is separate from syntax: enforce semantic bounds and valid combinations in the domain; let filesystem adapters perform actual reads and handle failures. Avoid existence-check-then-read races.

## Application and entry point

Use an Application class for orchestration with injected output streams, version provider and domain service. An exported `main(argv, dependencies): Promise<number>` can adapt that application for tests; only the executable bootstrap starts it.

- Bootstrap `src/main.ts` begins with `#!/usr/bin/env node`.
- Imports use `.js` for the compiled Node ESM profile.
- Handle `run/help/version` exhaustively; help/version must not require input or initialize external resources.
- Run async work in main/Application.run, await completion, close resources in finally. Importing a domain/parser module performs no process work.
- Use a handled startup promise; never leave a floating promise.

```typescript
// Executable bootstrap after constructing the application's dependencies:
application.run(process.argv.slice(2)).then(
  (code: number): void => {
    process.exitCode = code;
  },
  (error: unknown): void => {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exitCode = 2;
  },
);
```

This bootstrap fragment requires an actual application/dependencies; it is not a standalone program.

## Output, errors, and configuration

| Stream/code | Convention |
| --- | --- |
| stdout | Results/data; JSON by default for agent-facing tools |
| stderr | Diagnostics, warnings, progress; pino destination 2 when used |
| 0 | Success, help, version |
| 1 | Invalid arguments/input or an expected domain failure |
| 2 | Unexpected runtime failure |

Preserve established exit-code contracts. The Application boundary maps known input/domain errors to 1; unexpected failures reach the bootstrap. Prefer `process.exitCode` over `process.exit()` so streams/cleanup finish. Requested help/version normally goes to stdout; errors and accompanying usage go to stderr. Never write diagnostics into JSON output.

- Inject an output writer for unit tests; serialize one result per documented output contract.
- Read version from packaged metadata or a generated build constant tied to it. Resolve metadata relative to import.meta.url, then test both source and emitted layout; moving main to `dist/src/` changes relative paths.
- Parse config/JSON/env as `unknown` and validate before constructing readonly options. Define precedence explicitly: defaults, file, environment, arguments.
- Use the existing platform configuration-directory policy; agent skill CLIs may follow the skill-cli-development convention when applicable. Do not hard-code a general application to `~/.config/agent-skills`.
- Do not store/log secrets in examples. Credentials and network permissions require existing authorization.

## Behavioral checks

- Parser: valid argv, defaults, missing/invalid options, unknown flags, help/version without required input.
- Application: fake service and captured output; success, expected failure, unexpected rejection, cleanup.
- Compiled subprocess: successful JSON, clean stdout, stderr diagnostics, codes 0/1/2; use execFile/process.execPath without a shell.
- Installed bin: invoke the packed tool from a different working directory, test relative resources and version lookup. No reliance on tsx, source aliases, or undeclared root dependencies.
